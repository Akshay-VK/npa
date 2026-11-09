"""G2c Ticket 03: Rollout training on multi-particle world.

Trains the official NPA model (CPU shim) on multi-particle trajectories.
"""

import sys, os, time, json
sys.path.insert(0, "/mnt/d/dev/ai/experiments/npa")
sys.path.insert(0, "/home/akshay-vk/npa-work/code")

import torch
import numpy as np
import yaml

import npa_bruteforce
npa_bruteforce.install()

from models.npa import NPA, step_euler
from sphops import HashGrid
from npa.data.multiparticle import make_world

N = 16
ROLLOUT = 8
STEPS = 200
LR = 1e-3

torch.manual_seed(0)

world = make_world(n=N, seed=0)
ho_world = make_world(n=N, held_out=True, seed=0)

traj_xs, traj_vs = world.trajectory(ROLLOUT + 1, dt=0.01)
traj_xs = traj_xs.float()
x0 = traj_xs[0].unsqueeze(0)
s0 = torch.zeros(1, N, 16)

model = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
model.train()

grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                eps=0.1, num_particles=N, batch_size=1, max_particles_per_block=32)

opt = torch.optim.Adam(model.parameters(), lr=LR)

print(f"Training N={N}, rollout={ROLLOUT}, steps={STEPS}")
t0 = time.time()
for step in range(STEPS):
    opt.zero_grad()
    x, s = x0.clone(), s0.clone()
    loss = torch.tensor(0.0)
    for t in range(ROLLOUT):
        x, s, _ = step_euler(model, x, s, grid, dt=1.0)
        loss = loss + ((x - traj_xs[t + 1].unsqueeze(0)) ** 2).mean()
    loss = loss / ROLLOUT
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    if step % 50 == 0 or step == STEPS - 1:
        print(f"  step {step:4d}  loss {loss.item():.6f}  time {time.time()-t0:.1f}s")

model.eval()
with torch.no_grad():
    ho_xs, ho_vs = ho_world.trajectory(ROLLOUT + 1, dt=0.01)
    ho_xs = ho_xs.float()
    x, s = ho_xs[0].unsqueeze(0).clone(), torch.zeros(1, N, 16)
    ho_grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                       eps=0.1, num_particles=N, batch_size=1, max_particles_per_block=32)
    pred_xs = [x.squeeze(0).clone()]
    for t in range(ROLLOUT):
        x, s, _ = step_euler(model, x, s, ho_grid, dt=1.0)
        pred_xs.append(x.squeeze(0).clone())
    pred_traj = torch.stack(pred_xs)
    ref_traj = ho_xs[:ROLLOUT + 1]
    drift = (pred_traj - ref_traj).abs().mean().item() / (ref_traj.max() - ref_traj.min()).item()
    print(f"\n  rollout_drift: {drift:.4f}")

os.makedirs("runs/g2c_v1", exist_ok=True)
metrics = {"rollout_drift": drift, "final_loss": loss.item(), "n_particles": N, "rollout_steps": ROLLOUT}
with open("runs/g2c_v1/metrics.json", "w") as f:
    import json
    json.dump(metrics, f, indent=2)
print(f"  metrics: {metrics}")
print("  Done!")