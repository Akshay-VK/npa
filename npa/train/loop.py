"""Training loop. One function for every variant.

V2 (stateless): batched training on (x, E) pairs.
V3b (stateful): sequential training on trajectories, h evolves step by step.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import torch
import torch.nn as nn
import yaml

from npa.data.synthetic import make_world, harmonic_trajectory
from npa.eval.metrics import energy_mae, force_mae, rollout_drift


@dataclass
class Run:
    out_dir: Path
    metrics: dict = field(default_factory=dict)


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def train(config: dict, model, data_kind: str = "harmonic", held_out: bool = False) -> Run:
    seed = config.get("seed", 0)
    torch.manual_seed(seed)
    out_dir = Path(config.get("out_dir", "runs")) / config.get("name", "run") / f"seed{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "config.yaml", "w") as f:
        yaml.dump(config, f)
    with open(out_dir / "git_sha.txt", "w") as f:
        f.write(_git_sha())

    world = make_world(data_kind, seed=seed, held_out=False)
    ho_world = make_world(data_kind, seed=seed, held_out=True)

    is_latent = hasattr(model, "latent")

    lr = config.get("lr", 1e-3)
    steps = config.get("steps", 3000)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = torch.nn.MSELoss()

    model.train()

    if is_latent:
        # Sequential training: process trajectory step by step, h evolves
        n_traj = config.get("n_traj", 5)
        traj_len = config.get("traj_len", 500)
        for epoch in range(steps // traj_len):
            opt.zero_grad()
            total_loss = 0.0
            for ti in range(n_traj):
                xs, vs, Es = harmonic_trajectory(world, traj_len, seed=seed + ti)
                h = torch.zeros(model.latent)
                traj_loss = 0.0
                for t in range(traj_len):
                    x_t = xs[t].unsqueeze(0).unsqueeze(-1).float()
                    E_t = Es[t].unsqueeze(0).unsqueeze(-1).float()
                    pred_E = model.energy(x_t, h.unsqueeze(0))
                    traj_loss = traj_loss + loss_fn(pred_E, E_t)
                    v_t = torch.zeros(1, 1)
                    h = model.step_state(x_t, v_t, h.unsqueeze(0)).squeeze(0).detach()
                total_loss = total_loss + traj_loss / traj_len
            total_loss = total_loss / n_traj
            total_loss.backward()
            opt.step()
            if epoch % 5 == 0 or epoch == (steps // traj_len) - 1:
                print(f"  epoch {epoch:4d}  loss {total_loss.item():.6f}")
    else:
        # Batched training: random sampling on (x, E) pairs
        xs, vs, Es = harmonic_trajectory(world, config.get("n_steps", 3000), seed=seed)
        batch = config.get("batch", 64)
        n = len(xs)
        for step in range(steps):
            idx = torch.randint(0, n, (batch,))
            xb = xs[idx].unsqueeze(-1).float()
            Eb = Es[idx].unsqueeze(-1).float()
            opt.zero_grad()
            if hasattr(model, "force") and not hasattr(model, "energy"):
                Fb = torch.stack([world.force_conservative(x) for x in xs])[idx].unsqueeze(-1).float()
                pred_F = model.force(xb)
                loss = loss_fn(pred_F, Fb)
            else:
                pred_E = model.energy(xb)
                loss = loss_fn(pred_E, Eb)
            loss.backward()
            opt.step()
            if step % 500 == 0 or step == steps - 1:
                print(f"  step {step:5d}  loss {loss.item():.6f}")

    # Evaluate on held-out world
    model.eval()
    metrics = {}
    with torch.no_grad():
        xh, vh, Eh = harmonic_trajectory(ho_world, 500, seed=seed + 1)
        xh_t = xh.unsqueeze(-1).float()
        is_direct = hasattr(model, "force") and not hasattr(model, "energy")
        if is_direct:
            # Force targets from conservative force
            Fh = torch.stack([ho_world.force_conservative(x, t=i*0.01) for i, x in enumerate(xh)])
            pred_Fh = model.force(xh_t).squeeze(-1)
            metrics["force_mae"] = force_mae(pred_Fh, Fh.float())
        elif is_latent:
            h = torch.zeros(len(xh), model.latent)
            pred_Eh = model.energy(xh_t, h).squeeze(-1)
            metrics["energy_mae"] = energy_mae(pred_Eh, Eh.float())
        else:
            pred_Eh = model.energy(xh_t).squeeze(-1)
            metrics["energy_mae"] = energy_mae(pred_Eh, Eh.float())

        # Rollout drift: predict energy trajectory
        ref_traj = xh[:200]
        # For rollout, just compare energy predictions along reference trajectory
        if is_latent:
            h = torch.zeros(model.latent)
            preds = []
            for t in range(200):
                xt = xh[t].unsqueeze(0).unsqueeze(-1).float()
                preds.append(model.energy(xt, h.unsqueeze(0)).item())
                h = model.step_state(xt, torch.zeros(1, 1), h.unsqueeze(0)).squeeze(0).detach()
            pred_E_traj = torch.tensor(preds)
        else:
            pred_E_traj = model.energy(xh[:200].unsqueeze(-1).float()).squeeze(-1)
        ref_E_traj = Eh[:200]
        metrics["rollout_drift"] = rollout_drift(pred_E_traj, ref_E_traj)

    with open(out_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    run = Run(out_dir=out_dir, metrics=metrics)
    print(f"  metrics: {metrics}")
    return run