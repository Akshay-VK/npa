"""G2c: Multi-particle with SPH perception. Ticket 01 + 02 validation.

Tests that the official NPA model (with CPU shim) can do a forward pass
and generate multi-particle trajectories at small scale.
"""

import sys, os, time, resource
sys.path.insert(0, "/mnt/d/dev/ai/experiments/npa")
sys.path.insert(0, "/home/akshay-vk/npa-work/code")

import torch
import npa_bruteforce
npa_bruteforce.install()

from models.npa import NPA, step_euler
from sphops import HashGrid
from npa.data.multiparticle import make_world, energy_drift

# --- Ticket 01: Forward pass at N=64 ---
print("=" * 60)
print("Ticket 01: Forward pass at N=64")
print("=" * 60)

for N in [32, 64, 128]:
    torch.manual_seed(42)
    model = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
    model.eval()
    grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                    eps=0.1, num_particles=N, batch_size=1, max_particles_per_block=32)
    x = (torch.rand(1, N, 2) * 2 - 1) * 0.5
    s = torch.zeros(1, N, 16)

    t0 = time.perf_counter()
    with torch.no_grad():
        dx, ds, x_bin, s_bin = model(x, s, grid)
    dt = (time.perf_counter() - t0) * 1000
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    print(f"  N={N:4d}: forward={dt:7.1f}ms  peak={peak:6.0f}MB  dx={tuple(dx.shape)}")

# --- Ticket 02: Multi-particle world ---
print("\n" + "=" * 60)
print("Ticket 02: Multi-particle world")
print("=" * 60)

for N in [8, 32, 64]:
    w = make_world(n=N, seed=0)
    xs, vs = w.trajectory(500, dt=0.001)
    drift = energy_drift(w, xs, vs)
    print(f"  N={N:3d}: steps=500  energy_drift={drift:.2e}  x_range=[{xs.min():.2f}, {xs.max():.2f}]")

# Held-out
w_ho = make_world(n=8, held_out=True, seed=0)
print(f"  held-out: k_well={w_ho.k_well}, k_spring={w_ho.k_spring}")

# --- Forward pass on real trajectory data ---
print("\n" + "=" * 60)
print("Forward pass on trajectory data (N=64)")
print("=" * 60)
w = make_world(n=64, seed=0)
xs, vs = w.trajectory(10, dt=0.01)
model = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
model.eval()
grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                eps=0.1, num_particles=64, batch_size=1, max_particles_per_block=32)
x = xs[0].unsqueeze(0).float()
s = torch.zeros(1, 64, 16)
t0 = time.perf_counter()
with torch.no_grad():
    x2, s2, _ = step_euler(model, x, s, grid, dt=1.0)
dt = (time.perf_counter() - t0) * 1000
print(f"  Euler step: {dt:.1f}ms  x_range=[{x2.min():.3f}, {x2.max():.3f}]")
