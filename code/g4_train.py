"""G4 training: element-conditioned pair-energy model on Transition1x (or mock)."""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
import torch.nn as nn

from npa.data.transition1x import (Transition1xDataset, collate, make_mock_hdf5,
                                    barrier_kcal, reaction_energy_kcal,
                                    iter_reactions)
from npa.models.reactive import ReactivePairEnergy


def run_epoch(model, loader, opt, device, lam=1.0):
    model.train()
    tot = 0.0
    n = 0
    for batch in loader:
        z = batch["z"].to(device)
        x = batch["x"].to(device)
        mask = batch["mask"].to(device)
        ae = batch["atomization_energy"].to(device)
        F = batch["forces"].to(device)
        opt.zero_grad()
        e = model.energy(z, x, mask=mask)
        loss_e = ((e - ae) ** 2).mean()
        # force
        xf = x.detach().requires_grad_(True)
        ef = model.energy(z, xf, mask=mask)
        g = torch.autograd.grad(ef.sum(), xf, create_graph=True)[0]
        Fpred = -g
        # mask forces
        Fpred = Fpred * mask.unsqueeze(-1).float()
        Ftrue = F * mask.unsqueeze(-1).float()
        loss_f = ((Fpred - Ftrue) ** 2).mean()
        loss = loss_e + lam * loss_f
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        tot += loss.item()
        n += 1
    return tot / max(n, 1)


def eval_force_mae(model, loader, device):
    model.eval()
    errs = []
    for batch in loader:
        z = batch["z"].to(device)
        x = batch["x"].to(device)
        mask = batch["mask"].to(device)
        F = batch["forces"].to(device)
        xf = x.detach().requires_grad_(True)
        ef = model.energy(z, xf, mask=mask)
        g = torch.autograd.grad(ef.sum(), xf)[0]
        Fpred = -g
        m = mask.unsqueeze(-1).float()
        diff = (Fpred - F) * m
        errs.append(diff.abs().sum().item() / max(m.sum().item(), 1))
    return sum(errs) / max(len(errs), 1)


def eval_reaction_metrics(model, path, split, device, max_heavy=7):
    model.eval()
    b_errs, r_errs = [], []
    for r in iter_reactions(path, split=split, max_heavy=max_heavy):
        # reactant
        z = torch.tensor([r["reactant"]["atomic_numbers"]], dtype=torch.long, device=device)
        xr = torch.tensor(r["reactant"]["positions"], dtype=torch.float32, device=device).reshape(1, -1, 3)
        maskr = torch.ones(1, z.shape[1], dtype=torch.bool, device=device)
        er = model.energy(z, xr, mask=maskr).item()
        # ts
        zt = torch.tensor([r["transition_state"]["atomic_numbers"]], dtype=torch.long, device=device)
        xt = torch.tensor(r["transition_state"]["positions"], dtype=torch.float32, device=device).reshape(1, -1, 3)
        maskt = torch.ones(1, zt.shape[1], dtype=torch.bool, device=device)
        et = model.energy(zt, xt, mask=maskt).item()
        # product
        zp = torch.tensor([r["product"]["atomic_numbers"]], dtype=torch.long, device=device)
        xp = torch.tensor(r["product"]["positions"], dtype=torch.float32, device=device).reshape(1, -1, 3)
        maskp = torch.ones(1, zp.shape[1], dtype=torch.bool, device=device)
        ep = model.energy(zp, xp, mask=maskp).item()
        pred_barrier = (et - er) * 23.0605
        pred_re = (ep - er) * 23.0605
        true_barrier = barrier_kcal(r)
        true_re = reaction_energy_kcal(r)
        b_errs.append(abs(pred_barrier - true_barrier))
        r_errs.append(abs(pred_re - true_re))
    return {
        "barrier_mae_kcal": sum(b_errs) / len(b_errs) if b_errs else float("nan"),
        "reaction_energy_mae_kcal": sum(r_errs) / len(r_errs) if r_errs else float("nan"),
        "n_reactions": len(b_errs),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default=None)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--max-frames", type=int, default=4)
    ap.add_argument("--out", type=str, default="runs/g4_mock")
    args = ap.parse_args()

    if args.mock or args.data is None:
        fd, path = tempfile.mkstemp(suffix=".h5")
        os.close(fd)
        from npa.data.transition1x import make_mock_hdf5
        make_mock_hdf5(path)
        data_path = path
        print(f"using mock data: {path}")
    else:
        data_path = args.data

    from torch.utils.data import DataLoader
    tr = Transition1xDataset(data_path, split="train", max_frames=args.max_frames)
    va = Transition1xDataset(data_path, split="val", max_frames=args.max_frames)
    trl = DataLoader(tr, batch_size=args.batch, shuffle=True, collate_fn=collate)
    val = DataLoader(va, batch_size=args.batch, shuffle=False, collate_fn=collate)

    device = "cpu"
    model = ReactivePairEnergy(hidden=args.hidden).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    t0 = time.time()
    for ep in range(args.epochs):
        loss = run_epoch(model, trl, opt, device)
        fm = eval_force_mae(model, val, device)
        print(f"epoch {ep + 1}: loss={loss:.4f} val_force_mae={fm:.4f}")

    rm = eval_reaction_metrics(model, data_path, "test", device)
    print("test metrics:", rm)
    print(f"elapsed {time.time() - t0:.1f}s")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out / "model.pt")
    import json
    with open(out / "metrics.json", "w") as f:
        json.dump(rm, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    from pathlib import Path
    main()
