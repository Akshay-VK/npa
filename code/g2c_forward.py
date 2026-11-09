"""G2c Ticket 01: Forward pass at N=64.

Loads the official NPA model with the CPU shim, creates a 64-particle state,
runs one forward pass, reports timing + peak RSS.
"""

import time, resource, os, sys
sys.path.insert(0, "/mnt/d/dev/ai/experiments/npa")
sys.path.insert(0, "/home/akshay-vk/npa-work/code")

import torch
import npa_bruteforce
npa_bruteforce.install()

from models.npa import NPA, Pool
from sphops import HashGrid

N = 64
torch.manual_seed(42)

# Model
model = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
model.eval()

# Grid
grid = HashGrid(dim=2, boundary="clamped", mode="grid", grid_size=(8, 8),
                eps=0.1, num_particles=N, batch_size=1, max_particles_per_block=32)

# Seed: uniform circle
pool = Pool(device=torch.device("cpu"), pool_size=1, state_dims=16,
            num_particles=N, sigma=0.5, spatial_dims=2,
            seed_mode="uniform_circle", random_seed=42)
x, s = pool.seed_generator(1)

# Forward pass timing
t0 = time.perf_counter()
with torch.no_grad():
    dx, ds, x_bin, s_bin = model(x, s, grid)
dt = time.perf_counter() - t0

peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

print(f"N={N} particles")
print(f"Forward pass: {dt*1000:.1f} ms")
print(f"Peak RSS: {peak_mb:.1f} MB")
print(f"dx shape: {dx.shape}, ds shape: {ds.shape}")
print(f"Model params: {sum(p.numel() for p in model.parameters())}")

# Step timing (full Euler step)
t0 = time.perf_counter()
with torch.no_grad():
    from models.npa import step_euler
    x2, s2, _ = step_euler(model, x, s, grid)
dt2 = time.perf_counter() - t0
print(f"Euler step: {dt2*1000:.1f} ms")
