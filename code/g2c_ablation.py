"""G2c ablation: state_dims=1 (minimal) vs state_dims=16 (full NPA)."""

import sys, os, time
sys.path.insert(0, "/mnt/d/dev/ai/experiments/npa")
sys.path.insert(0, "/home/akshay-vk/npa-work/code")

import torch
import npa_bruteforce
npa_bruteforce.install()

from models.npa import NPA, step_euler
from sphops import HashGrid
from npa.data.multiparticle import make_world

def run(n, state_dims, steps=50, seed=0):
    torch.manual_seed(seed)
    world = make_world(n=n, seed=seed)
    ho_world = make_world(n=n, held_out=True, seed=seed)
    traj_xs, _ = world.trajectory(9, dt=0.01)
    traj_xs = traj_xs.float()
    x0 = traj_xs[0].unsqueeze(0)
    sd = max(state_dims, 1)
    s0 = torch.zeros(1, n, sd)

    model = NPA(spatial_dims=2, state_dims=sd, hidden_dims=128, eps0=0.1, alpha=0.5)
    model.train()
    grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                    eps=0.1, num_particles=n, batch_size=1, max_particles_per_block=32)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    for step in range(steps):
        opt.zero_grad()
        x, s = x0.clone(), s0.clone()
        loss = torch.tensor(0.0)
        for t in range(8):
            x, s, _ = step_euler(model, x, s, grid, dt=1.0)
            loss = loss + ((x - traj_xs[t + 1].unsqueeze(0)) ** 2).mean()
        loss = loss / 8
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

    model.eval()
    with torch.no_grad():
        ho_xs, _ = ho_world.trajectory(9, dt=0.01)
        ho_xs = ho_xs.float()
        x, s = ho_xs[0].unsqueeze(0).clone(), torch.zeros(1, n, sd)
        ho_grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                           eps=0.1, num_particles=n, batch_size=1, max_particles_per_block=32)
        pred_xs = [x.squeeze(0).clone()]
        for t in range(8):
            x, s, _ = step_euler(model, x, s, ho_grid, dt=1.0)
            pred_xs.append(x.squeeze(0).clone())
        pred_traj = torch.stack(pred_xs)
        ref_traj = ho_xs[:9]
        drift = (pred_traj - ref_traj).abs().mean().item() / (ref_traj.max() - ref_traj.min()).item()
    return drift

for sd in [1, 16]:
    drift = run(n=32, state_dims=sd, steps=50, seed=0)
    print(f"state_dims={sd:2d}: rollout_drift={drift:.4f}")