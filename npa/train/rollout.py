"""Rollout training loop for G2c. Trains NPA on trajectory MSE."""

from __future__ import annotations

import json, subprocess, time
from dataclasses import dataclass, field
from pathlib import Path

import torch
import torch.nn as nn
import yaml

from npa.data.multiparticle import make_world, energy_drift


@dataclass
class Run:
    out_dir: Path
    metrics: dict = field(default_factory=dict)


def _git_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def rollout_loss(model, x0, s0, grid, target_xs, n_steps):
    """MSE between predicted and target trajectory over n_steps."""
    from models.npa import step_euler
    x, s = x0.clone(), s0.clone()
    loss = torch.tensor(0.0)
    for t in range(n_steps):
        x, s, _ = step_euler(model, x, s, grid, dt=1.0)
        loss = loss + ((x - target_xs[t + 1]) ** 2).mean()
    return loss / n_steps


def train(config, model, world, held_out_world=None):
    import sys, os
    sys.path.insert(0, os.path.expanduser("~/npa-work/code"))
    import npa_bruteforce
    npa_bruteforce.install()

    seed = config.get("seed", 0)
    torch.manual_seed(seed)
    out_dir = Path(config.get("out_dir", "runs")) / config.get("name", "g2c") / f"seed{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "config.yaml", "w") as f:
        yaml.dump(config, f)
    with open(out_dir / "git_sha.txt", "w") as f:
        f.write(_git_sha())

    # Generate target trajectory
    n_steps = config.get("rollout_steps", 16)
    traj_xs, traj_vs = world.trajectory(n_steps + 1, dt=0.01)
    traj_xs = traj_xs.float()
    x0 = traj_xs[0].unsqueeze(0)  # (1, N, 2)
    s0 = torch.zeros(1, world.n, 16)

    from sphops import HashGrid
    grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                    eps=0.1, num_particles=world.n, batch_size=1, max_particles_per_block=32)

    lr = config.get("lr", 1e-3)
    steps = config.get("steps", 1000)
    opt = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for step in range(steps):
        opt.zero_grad()
        loss = rollout_loss(model, x0, s0, grid, traj_xs, n_steps)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % 100 == 0 or step == steps - 1:
            print(f"  step {step:5d}  loss {loss.item():.6f}")

    # Evaluate on held-out
    model.eval()
    metrics = {}
    with torch.no_grad():
        ho_xs, ho_vs = held_out_world.trajectory(n_steps + 1, dt=0.01)
        ho_xs = ho_xs.float()
        ho_x0 = ho_xs[0].unsqueeze(0)
        ho_s0 = torch.zeros(1, held_out_world.n, 16)
        ho_grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                           eps=0.1, num_particles=held_out_world.n, batch_size=1, max_particles_per_block=32)
        # Rollout
        from models.npa import step_euler
        x, s = ho_x0.clone(), ho_s0.clone()
        pred_xs = [x.squeeze(0).clone()]
        for t in range(n_steps):
            x, s, _ = step_euler(model, x, s, ho_grid, dt=1.0)
            pred_xs.append(x.squeeze(0).clone())
        pred_traj = torch.stack(pred_xs)
        ref_traj = ho_xs[:n_steps + 1]
        drift = (pred_traj - ref_traj).abs().mean().item() / (ref_traj.max() - ref_traj.min()).item()
        metrics["rollout_drift"] = drift
        metrics["final_loss"] = loss.item()

    with open(out_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    run = Run(out_dir=out_dir, metrics=metrics)
    print(f"  metrics: {metrics}")
    return run, model