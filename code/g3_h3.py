"""G3: can a model trained on cheap H3 labels predict the expensive barrier?

Reference reaction: collinear H + H2 -> H2 + H. Cheap labels are
CCSD(T)/cc-pVDZ, the reference is CCSD(T)/cc-pVTZ, and MP2/cc-pVTZ is a
negative control (a cheaper method that gets the barrier wrong). The model
sees only the three pairwise H-H distances, so rotation and translation
invariance are exact by construction.

Usage:
    python code/g3_h3.py --generate --steps 3000 --seeds 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch
import torch.nn.functional as F

from npa.data.h3 import (GRID, HARTREE2KCAL, REACTANT, SADDLE, h3_positions,
                         scan)
from npa.models.molecular import build_molecular

LEVELS = {
    "cheap": "ccsd(t)/cc-pvdz",
    "ref": "ccsd(t)/cc-pvtz",
    "mp2": "mp2/cc-pvtz",
}
LOW_ENERGY = 60.0  # kcal/mol; the repulsive wall above this is not the gate.


def to_xy(data: dict) -> tuple[torch.Tensor, torch.Tensor, dict]:
    """Positions (N,3,3), relative energies (N,) in kcal/mol, and index map."""
    r1, r2 = data["r1"], data["r2"]
    x = torch.tensor(np.stack([h3_positions(a, b) for a, b in zip(r1, r2)]),
                     dtype=torch.float32)
    e = torch.tensor(data["energy"], dtype=torch.float64)
    idx = {
        "reactant": int(np.where(np.isclose(r1, REACTANT[0]) &
                                 np.isclose(r2, REACTANT[1]))[0][0]),
        "saddle": int(np.where(np.isclose(r1, SADDLE[0]) &
                               np.isclose(r2, SADDLE[1]))[0][0]),
    }
    e0 = e[idx["reactant"]]
    y = ((e - e0) * HARTREE2KCAL).to(torch.float32)
    # Dissociation probe: H at 6 A, H2 at its equilibrium bond.
    idx["far"] = int(np.where(np.isclose(r1, 6.0) &
                              np.isclose(r2, REACTANT[1]))[0][0])
    return x, y, idx


def train_model(x: torch.Tensor, y: torch.Tensor, kind: str, steps: int,
                seed: int, lr: float) -> torch.nn.Module:
    torch.manual_seed(seed)
    model = build_molecular(kind)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    model.train()
    for _ in range(steps):
        opt.zero_grad()
        loss = F.huber_loss(model(x), y, delta=5.0)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    model.eval()
    return model


@torch.no_grad()
def evaluate(model: torch.nn.Module, x: torch.Tensor, y: torch.Tensor,
             idx: dict, mask: torch.Tensor) -> dict:
    pred = model(x)
    barrier_pred = (pred[idx["saddle"]] - pred[idx["reactant"]]).item()
    barrier_ref = (y[idx["saddle"]] - y[idx["reactant"]]).item()
    diss_pred = (pred[idx["far"]] - pred[idx["reactant"]]).item()
    diss_ref = (y[idx["far"]] - y[idx["reactant"]]).item()
    err = (pred[mask] - y[mask]).abs()
    return {
        "barrier_pred": barrier_pred,
        "barrier_ref": barrier_ref,
        "barrier_err": abs(barrier_pred - barrier_ref),
        "energy_mae": err.mean().item(),
        "energy_rmse": err.pow(2).mean().sqrt().item(),
        "diss_pred": diss_pred,
        "diss_ref": diss_ref,
        "diss_err": abs(diss_pred - diss_ref),
    }


@torch.no_grad()
def rotation_error(model: torch.nn.Module, x: torch.Tensor) -> float:
    """Rotate every geometry by the same random proper rotation."""
    a = torch.randn(3, 3, dtype=x.dtype)
    q, _ = torch.linalg.qr(a)
    r = q * torch.sign(torch.det(q))
    return (model(x) - model(x @ r.T)).abs().max().item()


def summarise(rows: list[dict]) -> dict:
    keys = ["barrier_pred", "barrier_ref", "barrier_err", "energy_mae",
            "energy_rmse", "diss_pred", "diss_ref", "diss_err", "rot_err"]
    out = {}
    for k in keys:
        vals = torch.tensor([r[k] for r in rows], dtype=torch.float64)
        out[k] = {"mean": vals.mean().item(), "std": vals.std().item()}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--lr", type=float, default=5e-3)
    ap.add_argument("--models", nargs="+", default=["mlp", "pairwise"])
    ap.add_argument("--out", default="runs/g3_h3/results.json")
    args = ap.parse_args()

    if args.generate:
        for name, level in LEVELS.items():
            t0 = time.time()
            print(f"generating {name}: {level}", flush=True)
            scan(level)
            print(f"  done in {time.time() - t0:.1f}s", flush=True)

    data = {name: to_xy(scan(level, verbose=False)) for name, level in LEVELS.items()}
    x_cheap, y_cheap, idx_cheap = data["cheap"]
    x_ref, y_ref, idx_ref = data["ref"]
    x_mp2, y_mp2, idx_mp2 = data["mp2"]

    cheap_mask = y_cheap < LOW_ENERGY
    ref_mask = y_ref < LOW_ENERGY
    mp2_mask = y_mp2 < LOW_ENERGY
    # Spatial hold-out around the saddle: the model must interpolate the ridge.
    r1, r2 = np.meshgrid(GRID, GRID, indexing="ij")
    holdout = torch.tensor(((r1 >= 0.85) & (r1 <= 1.05) &
                            (r2 >= 0.85) & (r2 <= 1.05)).reshape(-1))
    ref_train = ref_mask & ~holdout

    conditions = {
        # Cheap labels everywhere; the expensive reference is never seen.
        "cheap_to_ref": (x_cheap[cheap_mask], y_cheap[cheap_mask],
                         x_ref, y_ref, idx_ref, ref_mask),
        # Cheaper method, same basis: the negative control.
        "mp2_to_ref": (x_mp2[mp2_mask], y_mp2[mp2_mask],
                       x_ref, y_ref, idx_ref, ref_mask),
        # Reference labels, saddle region held out: architecture interpolation.
        "ref_holdout": (x_ref[ref_train], y_ref[ref_train],
                        x_ref, y_ref, idx_ref, ref_mask & holdout),
    }

    results = {"config": vars(args), "levels": LEVELS,
               "n_train": int(cheap_mask.sum()), "n_eval": int(ref_mask.sum()),
               "barrier_ref": float(y_ref[idx_ref["saddle"]] - y_ref[idx_ref["reactant"]]),
               "runs": {}}
    for kind in args.models:
        results["runs"][kind] = {}
        for cond, (xtr, ytr, xev, yev, idx, mask) in conditions.items():
            rows = []
            for seed in range(args.seeds):
                t0 = time.time()
                model = train_model(xtr, ytr, kind, args.steps, seed, args.lr)
                row = evaluate(model, xev, yev, idx, mask)
                row["rot_err"] = rotation_error(model, xev[mask][:32])
                row["seed"] = seed
                row["train_time"] = time.time() - t0
                rows.append(row)
                print(f"{kind:9s} {cond:12s} seed {seed}: "
                      f"barrier {row['barrier_pred']:.2f} vs {row['barrier_ref']:.2f} "
                      f"(err {row['barrier_err']:.2f}), mae {row['energy_mae']:.2f}, "
                      f"diss {row['diss_pred']:.2f}, rot {row['rot_err']:.1e}",
                      flush=True)
            results["runs"][kind][cond] = {"rows": rows, "summary": summarise(rows)}

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=2))
    print(f"\nwrote {args.out}")
    for kind, conds in results["runs"].items():
        for cond, r in conds.items():
            s = r["summary"]
            print(f"{kind:9s} {cond:12s} barrier {s['barrier_pred']['mean']:.2f} "
                  f"± {s['barrier_pred']['std']:.2f} vs {s['barrier_ref']['mean']:.2f}, "
                  f"err {s['barrier_err']['mean']:.2f}, "
                  f"mae {s['energy_mae']['mean']:.2f}, "
                  f"diss_err {s['diss_err']['mean']:.2f}, "
                  f"rot {s['rot_err']['mean']:.1e}")


if __name__ == "__main__":
    main()
