"""G2e: does a fixed latent state beat a stateless history baseline?

Runs the G2d world with improved state arms and a stateless history control.
See .scratch/wiki/g2e.md for the full design and pass/fail rule.
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
from npa.models.mp_variants import build_variant as build_base
from npa.models.mp_g2e import build_variant as build_g2e


def _is_stateful(kind):
    return kind in ("v3b", "v3b_sup", "v3b_ema", "v3b_residual",
                    "v3b_combined")


def _is_history(kind):
    return kind == "v2h"


def _state_dim(kind, cfg):
    if kind == "v2h":
        return (cfg["history"], 2)
    if _is_stateful(kind):
        return cfg["state_dim"]
    return None


def _make_state(kind, cfg, device="cpu"):
    if kind == "v2h":
        k, d = cfg["history"], 2
        return torch.zeros(1, cfg["n"], k, d)
    if _is_stateful(kind):
        return torch.zeros(1, cfg["n"], cfg["state_dim"])
    return None


def _build(kind, cfg):
    if kind in ("v1", "v2", "oracle"):
        return build_base(kind, dim=2, hidden=cfg["hidden"],
                          state_dim=cfg["state_dim"])
    if kind == "v3b" or kind == "v3b_sup":
        return build_base(kind, dim=2, hidden=cfg["hidden"],
                          state_dim=cfg["state_dim"])
    if kind in ("v3b_ema", "v3b_residual", "v3b_combined"):
        return build_g2e(kind, dim=2, hidden=cfg["hidden"],
                         state_dim=cfg["state_dim"], k_well=1.0)
    if kind == "v2h":
        return build_g2e(kind, dim=2, hidden=cfg["hidden"])
    raise ValueError(kind)


def _step(model, kind, x, s, qs_t, dt, cfg):
    if kind == "oracle":
        F = model.force(x, qs_t.unsqueeze(0))
        return x + F * dt, s, F
    if kind == "v1":
        F = model.force(x)
        return x + F * dt, s, F
    if kind == "v2":
        F = model.force(x)
        return x + F * dt, s, F
    if kind == "v2h":
        F, ds = model.force_and_ds(x, s)
        return x + F * dt, s + ds, F
    # stateful
    F, ds = model.force_and_ds(x, s)
    return x + F * dt, s + ds, F


def _q_features(q):
    return torch.stack([torch.cos(q), torch.sin(q)], dim=-1)


def force_rollout(model, kind, world, xs, qs, steps, dt, cfg):
    state_dim = cfg["state_dim"]
    if kind == "v2h":
        s = torch.zeros(1, xs.shape[1], cfg["history"], 2)
    elif _is_stateful(kind):
        s = torch.zeros(1, xs.shape[1], state_dim)
    else:
        s = None
    loss = torch.tensor(0.0)
    for t in range(steps):
        xt = xs[t].unsqueeze(0)
        if kind == "oracle":
            F = model.force(xt, qs[t].unsqueeze(0))
        elif kind in ("v2h",) or _is_stateful(kind):
            F, ds = model.force_and_ds(xt, s)
            s = s + ds
        else:
            F = model.force(xt)
        loss = loss + ((F - world.force(xs[t], qs[t]).unsqueeze(0)) ** 2).mean()
    return loss / steps


def rollout(model, kind, x0, qs, target, steps, dt, cfg, aux_weight=0.0,
            probe=None, true_forces=None, force_weight=0.0):
    if kind == "v2h":
        s = torch.zeros(1, x0.shape[1], cfg["history"], 2)
    elif _is_stateful(kind):
        s = torch.zeros(1, x0.shape[1], cfg["state_dim"])
    else:
        s = None
    x = x0.clone()
    loss_pos = torch.tensor(0.0)
    loss_force = torch.tensor(0.0)
    for t in range(steps):
        x, s, F = _step(model, kind, x, s, qs[t], dt, cfg)
        loss_pos = loss_pos + ((x - target[t + 1].unsqueeze(0)) ** 2).mean()
        if force_weight > 0.0 and true_forces is not None:
            loss_force = loss_force + ((F - true_forces[t].unsqueeze(0)) ** 2).mean()
        if aux_weight > 0.0 and probe is not None and _is_stateful(kind):
            qf = _q_features(qs[t + 1]).unsqueeze(0)
            loss_pos = loss_pos + aux_weight * ((probe(s) - qf) ** 2).mean()
    return loss_pos / steps + force_weight * loss_force / steps


def train_one(kind, world, cfg, seed):
    torch.manual_seed(seed)
    model = _build(kind, cfg)
    probe = None
    if kind == "v3b_sup":
        probe = nn.Linear(cfg["state_dim"], 2)
    params = list(model.parameters())
    if probe is not None:
        params = params + list(probe.parameters())
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
        tf = [world.force(xs[t], qs[t]) for t in range(cfg["rollout"])]
        true_forces = torch.stack(tf)
        loss = rollout(model, kind, xs[0].unsqueeze(0), qs, xs, cfg["rollout"],
                       dt, cfg, probe=probe, aux_weight=aux_weight,
                       true_forces=true_forces, force_weight=cfg["force_weight"])
        loss = loss + cfg["force_weight"] * force_rollout(
            model, kind, world, xs, qs, cfg["rollout"], dt, cfg)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
    return model, probe, time.time() - t0


@torch.no_grad()
def evaluate(model, kind, worlds, cfg):
    dt = cfg["dt"]
    H = cfg["eval_rollout"]
    drifts, finals, force_maes, r2s = [], [], [], []
    for world in worlds:
        xs, _vs, qs = world.trajectory(H + 1, dt)
        x = xs[0].unsqueeze(0).clone()
        if kind == "v2h":
            s = torch.zeros(1, xs.shape[1], cfg["history"], 2)
        elif _is_stateful(kind):
            s = torch.zeros(1, xs.shape[1], cfg["state_dim"])
        else:
            s = None
        preds = [x.squeeze(0).clone()]
        states, targets = [], []
        for t in range(H):
            x, s, F = _step(model, kind, x, s, qs[t], dt, cfg)
            preds.append(x.squeeze(0).clone())
            if _is_stateful(kind):
                states.append(s.squeeze(0).clone())
                targets.append(_q_features(qs[t + 1]))
            xt = xs[t].unsqueeze(0)
            if kind == "oracle":
                Fm = model.force(xt, qs[t].unsqueeze(0))
            elif kind == "v2h":
                Fm = model.force(xt, s)
            elif _is_stateful(kind):
                Fm, _ = model.force_and_ds(xt, s)
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


def build_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--variants", nargs="+",
                    default=["v1", "v2", "v2h", "v3b", "v3b_sup", "v3b_ema",
                             "v3b_residual", "v3b_combined", "oracle"])
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--rollout", type=int, default=16)
    ap.add_argument("--eval-rollout", type=int, default=32)
    ap.add_argument("--out", type=str, default="runs/g2e")
    ap.add_argument("--seed", type=int, default=None,
                    help="Run a single seed (for parallelism).")
    ap.add_argument("--variant", type=str, default=None,
                    help="Run a single variant (for parallelism).")
    ap.add_argument("--state-dim", dest="state_dim", type=int, default=4,
                    help="Latent state dimension (default 4).")
    return ap


def parse_args(argv=None):
    return build_parser().parse_args(argv)


# Aliases for callers/tests that use other names.
make_parser = build_parser
get_parser = build_parser


def main():
    args = parse_args()

    cfg = {
        "steps": args.steps, "rollout": args.rollout, "eval_rollout": args.eval_rollout,
        "dt": 0.01, "lr": 1e-3, "hidden": 64, "state_dim": args.state_dim, "n_train": 8,
        "aux_weight": 0.1, "force_weight": 1.0, "history": 4, "n": args.n,
    }
    ks = 0.0
    world = make_world(n=args.n, seed=0, k_spring=ks)
    worlds_eval = [make_world(n=args.n, seed=100 + s, k_spring=ks) for s in range(4)]
    worlds_shift = [make_world(n=args.n, held_out=True, seed=200 + s, k_spring=ks)
                    for s in range(4)]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    variants = [args.variant] if args.variant else args.variants
    seeds = [args.seed] if args.seed is not None else list(range(args.seeds))

    results = {}
    for kind in variants:
        runs = []
        for seed in seeds:
            model, probe, t = train_one(kind, world, cfg, seed)
            m = evaluate(model, kind, worlds_eval, cfg)
            ms = evaluate(model, kind, worlds_shift, cfg)
            m.update(seed=seed, train_time=t,
                     param_shift_drift=ms["rollout_drift"],
                     param_shift_force_mae=ms["force_mae"],
                     params=sum(p.numel() for p in model.parameters()) +
                     (sum(p.numel() for p in probe.parameters()) if probe else 0))
            runs.append(m)
            print(f"  {kind:16s} seed {seed}: drift={m['rollout_drift']:.4f} "
                  f"force_mae={m['force_mae']:.4f} state_r2={m['state_r2']}")
            # Save per-run shard for parallelism.
            shard = out_dir / f"shard_{kind}_{seed}.json"
            with open(shard, "w") as f:
                json.dump({kind: {"runs": [m]}}, f, indent=2)
        # Aggregate if all seeds present.
        agg = {}
        for key in ("rollout_drift", "final_drift", "force_mae"):
            vals = [r[key] for r in runs]
            if vals:
                mu = sum(vals) / len(vals)
                agg[key] = {"mean": mu,
                            "std": (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5}
        r2s = [r["state_r2"] for r in runs if r["state_r2"] is not None]
        agg["state_r2"] = {"mean": sum(r2s) / len(r2s)} if r2s else None
        agg["params"] = runs[0]["params"] if runs else 0
        results[kind] = {"runs": runs, "agg": agg}

    # Merge with any existing results.json.
    rpath = out_dir / "results.json"
    if rpath.exists():
        old = json.loads(rpath.read_text())
        for k, v in results.items():
            if k in old and "runs" in old[k]:
                # Merge runs by seed.
                existing_seeds = {r["seed"] for r in old[k]["runs"]}
                new_runs = [r for r in v["runs"] if r["seed"] not in existing_seeds]
                old[k]["runs"].extend(new_runs)
                # Recompute agg.
                runs = old[k]["runs"]
                agg = {}
                for key in ("rollout_drift", "final_drift", "force_mae"):
                    vals = [r[key] for r in runs]
                    if vals:
                        mu = sum(vals) / len(vals)
                        agg[key] = {"mean": mu,
                                    "std": (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5}
                r2s = [r["state_r2"] for r in runs if r["state_r2"] is not None]
                agg["state_r2"] = {"mean": sum(r2s) / len(r2s)} if r2s else None
                agg["params"] = runs[0]["params"] if runs else 0
                old[k]["agg"] = agg
            else:
                old[k] = v
        results = old

    with open(rpath, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {rpath}")
    print("\n=== summary (mean over seeds) ===")
    for kind, r in results.items():
        a = r["agg"]
        print(f"{kind:16s} params={a['params']:5d} drift={a['rollout_drift']['mean']:.4f} "
              f"force_mae={a['force_mae']['mean']:.4f} state_r2="
              f"{a['state_r2']['mean'] if a['state_r2'] else 'n/a'}")


if __name__ == "__main__":
    main()
