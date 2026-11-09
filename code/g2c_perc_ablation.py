"""G2c ablation: SPH perception on vs off.

Compares full NPA (with SPH perception) to a model that uses raw positions only.
"""

import sys, os, time
sys.path.insert(0, "/mnt/d/dev/ai/experiments/npa")
sys.path.insert(0, "/home/akshay-vk/npa-work/code")

import torch
import torch.nn as nn
import npa_bruteforce
npa_bruteforce.install()

from models.npa import NPA, step_euler
from sphops import HashGrid
from npa.data.multiparticle import make_world


class NoPerceptionModel(nn.Module):
    """MLP on raw (x, s) without SPH perception. Baseline for perception ablation."""
    def __init__(self, spatial_dims=2, state_dims=16, hidden_dims=128):
        super().__init__()
        self.spatial_dims = spatial_dims
        self.state_dims = state_dims
        in_dim = spatial_dims + state_dims
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dims), nn.Tanh(),
            nn.Linear(hidden_dims, hidden_dims), nn.Tanh(),
            nn.Linear(hidden_dims, spatial_dims + state_dims),
        )
        self.alpha = 0.5

    def forward(self, x, s, grid=None):
        B, N, _ = x.shape
        C = s.shape[-1]
        inp = torch.cat([x, s], dim=-1)  # (B, N, dim+C)
        y = self.net(inp)  # (B, N, dim+C)
        dx = y[..., :self.spatial_dims]
        ds = y[..., self.spatial_dims:]
        dx = self.alpha * dx / (1.0 + dx.norm(dim=-1, keepdim=True))
        return dx, ds, x, s

    def step(self, x, s, grid=None, dt=1.0):
        dx, ds, x_bin, s_bin = self.forward(x, s, grid)
        x = x_bin + dt * dx
        s = s_bin + dt * ds
        return x, s, None


def run(use_perception, n=32, steps=50, seed=0):
    torch.manual_seed(seed)
    world = make_world(n=n, seed=seed)
    ho_world = make_world(n=n, held_out=True, seed=seed)
    traj_xs, _ = world.trajectory(9, dt=0.01)
    traj_xs = traj_xs.float()
    x0 = traj_xs[0].unsqueeze(0)
    s0 = torch.zeros(1, n, 16)

    if use_perception:
        model = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
    else:
        model = NoPerceptionModel(spatial_dims=2, state_dims=16, hidden_dims=128)

    model.train()
    grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                    eps=0.1, num_particles=n, batch_size=1, max_particles_per_block=32)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    for step in range(steps):
        opt.zero_grad()
        x, s = x0.clone(), s0.clone()
        loss = torch.tensor(0.0)
        for t in range(8):
            if use_perception:
                x, s, _ = step_euler(model, x, s, grid, dt=1.0)
            else:
                x, s, _ = model.step(x, s, grid, dt=1.0)
            loss = loss + ((x - traj_xs[t + 1].unsqueeze(0)) ** 2).mean()
        loss = loss / 8
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

    # Evaluate
    model.eval()
    with torch.no_grad():
        ho_xs, _ = ho_world.trajectory(9, dt=0.01)
        ho_xs = ho_xs.float()
        x, s = ho_xs[0].unsqueeze(0).clone(), torch.zeros(1, n, 16)
        ho_grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                           eps=0.1, num_particles=n, batch_size=1, max_particles_per_block=32)
        pred_xs = [x.squeeze(0).clone()]
        for t in range(8):
            if use_perception:
                x, s, _ = step_euler(model, x, s, ho_grid, dt=1.0)
            else:
                x, s, _ = model.step(x, s, ho_grid, dt=1.0)
            pred_xs.append(x.squeeze(0).clone())
        pred_traj = torch.stack(pred_xs)
        ref_traj = ho_xs[:9]
        drift = (pred_traj - ref_traj).abs().mean().item() / (ref_traj.max() - ref_traj.min()).item()
    return drift

for perc in [True, False]:
    drift = run(use_perception=perc, n=32, steps=50, seed=0)
    label = "with perception" if perc else "without perception"
    print(f"{label}: rollout_drift={drift:.4f}")