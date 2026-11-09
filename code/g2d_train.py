"""G2d: does persistent latent state help when memory is necessary?

World: multi-particle with a hidden per-particle phase (see npa/data/hidden_force.py).
Arms: V1 direct, V2 stateless energy, V3b latent energy, V3b+supervised state
(diagnostic), and an oracle energy model that sees the true phase (ceiling).

Usage:
    python code/g2d_train.py --steps 400 --seeds 3 --variants v1 v2 v3b v3b_sup oracle
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
import torch.nn as nn

from npa.data.hidden_force import make_world
from npa.models.mp_variants import build_variant


def _q_features(q: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch.cos(q), torch.sin(q)], dim=-1)


def _step(model, kind, x, s, q_t, dt):
    """One model step. Returns (x, s, force_estimate)."""
    if kind == "oracle":
        F = model.force(x, q_t.unsqueeze(0))
        return x + F * dt, s, F
    if kind == "v1":
        F = model.force(x)
        return x + F * dt, s, F
    if kind in ("v3b", "v3b_sup"):
        return model.step(x, s, dt)
    return model.step(x, s, dt)


def force_rollout(model, kind, world, xs, qs, steps, dt, state_dim):
    """Teacher-forced force loss: state is updated from the true positions."""
    s = torch.zeros(1, xs.shape[1], state_dim) if kind in ("v3b", "v3b_sup") else None
    loss = torch.tensor(0.0)
    for t in range(steps):
        xt = xs[t].unsqueeze(0)
        if kind == "oracle":
            F = model.force(xt, qs[t].unsqueeze(0))
        elif kind in ("v3b", "v3b_sup"):
            F, ds = model.force_and_ds(xt, s)
            s = s + ds
        elif kind == "v1":
            F = model.force(xt)
        else:
            F = model.force(xt)
        loss = loss + ((F - world.force(xs[t], qs[t]).unsqueeze(0)) ** 2).mean()
    return loss / steps


def rollout(model, kind, x0, qs, target, steps, dt, state_dim,
            probe=None, aux_weight=0.0, true_forces=None, force_weight=0.0):
    x = x0.clone()
    s = torch.zeros(1, x.shape[1], state_dim) if kind in ("v3b", "v3b_sup") else None
    loss_pos = torch.tensor(0.0)
    loss_force = torch.tensor(0.0)
    for t in range(steps):
        x, s, F = _step(model, kind, x, s, qs[t], dt)
        loss_pos = loss_pos + ((x - target[t + 1].unsqueeze(0)) ** 2).mean()
        if force_weight > 0.0 and true_forces is not None:
            loss_force = loss_force + ((F - true_forces[t].unsqueeze(0)) ** 2).mean()
        if aux_weight > 0.0 and probe is not None:
            qf = _q_features(qs[t + 1]).unsqueeze(0)
            loss_pos = loss_pos + aux_weight * ((probe(s) - qf) ** 2).mean()
    return loss_pos / steps + force_weight * loss_force / steps


def train_one(kind, world, cfg, seed):
    torch.manual_seed(seed)
    model = build_variant(kind, dim=2, hidden=cfg["hidden"], state_dim=cfg["state_dim"])
    probe = nn.Linear(cfg["state_dim"], 2) if kind == "v3b_sup" else None
    params = list(model.parameters()) + (list(probe.parameters()) if probe else [])
    opt = torch.optim.Adam(params, lr=cfg["lr"])
    dt = cfg["dt"]
    state_dim = cfg["state_dim"]
    aux_weight = cfg["aux_weight"] if kind == "v3b_sup" else 0.0

    trajs = [world.trajectory(cfg["rollout"] + 1, dt) for _ in range(cfg["n_train"])]
    model.train()
    t0 = time.time()
    for step in range(cfg["steps"]):
        i = step % len(trajs)
        xs, _vs, qs = trajs[i]
        opt.zero_grad()
        loss = rollout(model, kind, xs[0].unsqueeze(0), qs, xs, cfg["rollout"],
                       dt, state_dim, probe=probe, aux_weight=aux_weight)
        loss = loss + cfg["force_weight"] * force_rollout(
            model, kind, world, xs, qs, cfg["rollout"], dt, state_dim)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
    return model, probe, time.time() - t0


@torch.no_grad()
def evaluate(model, kind, worlds, cfg):
    dt = cfg["dt"]
    state_dim = cfg["state_dim"]
    H = cfg["eval_rollout"]
    drifts, finals, force_maes, r2s = [], [], [], []
    for world in worlds:
        xs, _vs, qs = world.trajectory(H + 1, dt)
        x = xs[0].unsqueeze(0).clone()
        s = torch.zeros(1, xs.shape[1], state_dim) if kind in ("v3b", "v3b_sup") else None
        preds = [x.squeeze(0).clone()]
        states, targets = [], []
        for t in range(H):
            x, s, F = _step(model, kind, x, s, qs[t], dt)
            preds.append(x.squeeze(0).clone())
            if kind in ("v3b", "v3b_sup"):
                states.append(s.squeeze(0).clone())
                targets.append(_q_features(qs[t + 1]))
            # Force error at the true position, using the current state.
            xt = xs[t].unsqueeze(0)
            if kind == "oracle":
                Fm = model.force(xt, qs[t].unsqueeze(0))
            elif kind in ("v3b", "v3b_sup"):
                Fm, _ = model.force_and_ds(xt, s)
            elif kind == "v1":
                Fm = model.force(xt)
            else:
                Fm = model.force(xt)
            true_F = world.force(xs[t], qs[t])
            force_maes.append((Fm.squeeze(0) - true_F).abs().mean().item())
        pred = torch.stack(preds)
        ref = xs[:H + 1]
        amp = (ref.max() - ref.min()).item()
        drifts.append((pred - ref).abs().mean().item() / amp)
        finals.append((pred[-1] - ref[-1]).abs().mean().item() / amp)
        if states:
            S = torch.cat(states, 0)
            T = torch.cat(targets, 0)
            S = torch.cat([S, torch.ones(S.shape[0], 1)], 1)
            coef = torch.linalg.lstsq(S, T).solution
            pred_t = S @ coef
            ss_res = ((T - pred_t) ** 2).sum()
            ss_tot = ((T - T.mean(0)) ** 2).sum().clamp(min=1e-9)
            r2s.append((1 - ss_res / ss_tot).item())
    return {
        "rollout_drift": sum(drifts) / len(drifts),
        "final_drift": sum(finals) / len(finals),
        "force_mae": sum(force_maes) / len(force_maes),
        "state_r2": sum(r2s) / len(r2s) if r2s else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--variants", nargs="+", default=["v1", "v2", "v3b", "v3b_sup", "oracle"])
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--k-spring", type=float, default=0.0)
    ap.add_argument("--rollout", type=int, default=16)
    ap.add_argument("--eval-rollout", type=int, default=32)
    ap.add_argument("--out", type=str, default="runs/g2d")
    args = ap.parse_args()

    cfg = {
        "steps": args.steps, "rollout": args.rollout, "eval_rollout": args.eval_rollout,
        "dt": 0.01, "lr": 1e-3, "hidden": 64, "state_dim": 4, "n_train": 8,
        "aux_weight": 0.1, "force_weight": 1.0,
    }
    ks = args.k_spring
    world = make_world(n=args.n, seed=0, k_spring=ks)
    # Same dynamics, new initial conditions: the fair test of memory.
    worlds_eval = [make_world(n=args.n, seed=100 + s, k_spring=ks) for s in range(4)]
    # Shifted dynamics: a robustness stress test, not the gate.
    worlds_shift = [make_world(n=args.n, held_out=True, seed=200 + s, k_spring=ks)
                    for s in range(4)]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for kind in args.variants:
        runs = []
        for seed in range(args.seeds):
            model, probe, t = train_one(kind, world, cfg, seed)
            m = evaluate(model, kind, worlds_eval, cfg)
            ms = evaluate(model, kind, worlds_shift, cfg)
            m.update(seed=seed, train_time=t,
                     param_shift_drift=ms["rollout_drift"],
                     param_shift_force_mae=ms["force_mae"],
                     params=sum(p.numel() for p in model.parameters()) +
                     (sum(p.numel() for p in probe.parameters()) if probe else 0))
            runs.append(m)
            print(f"  {kind:8s} seed {seed}: drift={m['rollout_drift']:.4f} "
                  f"force_mae={m['force_mae']:.4f} state_r2={m['state_r2']}")
        agg = {}
        for key in ("rollout_drift", "final_drift", "force_mae"):
            vals = [r[key] for r in runs]
            mu = sum(vals) / len(vals)
            agg[key] = {"mean": mu,
                        "std": (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5}
        r2s = [r["state_r2"] for r in runs if r["state_r2"] is not None]
        agg["state_r2"] = {"mean": sum(r2s) / len(r2s)} if r2s else None
        agg["params"] = runs[0]["params"]
        results[kind] = {"runs": runs, "agg": agg}

    with open(out_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n=== summary (mean over seeds) ===")
    for kind, r in results.items():
        a = r["agg"]
        print(f"{kind:8s} params={a['params']:5d} drift={a['rollout_drift']['mean']:.4f} "
              f"force_mae={a['force_mae']['mean']:.4f} state_r2="
              f"{a['state_r2']['mean'] if a['state_r2'] else 'n/a'}")
    print(f"\nwrote {out_dir / 'results.json'}")


if __name__ == "__main__":
    main()
