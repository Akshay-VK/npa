"""Control experiment: stateless model with velocity input.

Tests whether velocity information helps (independent of state mechanism).
If this works, the question is whether V3b's state can match it.
"""

import sys, os, time
sys.path.insert(0, "/mnt/d/dev/ai/experiments/npa/code")
import torch, torch.nn as nn
import numpy as np

# Import from g2b_experiment
from g2b_experiment import make_damped_world, langevin_traj, evaluate

class DirectWithVelocity(nn.Module):
    def __init__(self, hidden=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )
    def force(self, x, v):
        return self.net(torch.cat([x, v], dim=-1))

world = make_damped_world(held_out=False, seed=0)
ho_world = make_damped_world(held_out=True, seed=0)

# Train
torch.manual_seed(0)
xs, vs, Fs = langevin_traj(world, 5000, seed=0)
model = DirectWithVelocity(hidden=64)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()
n = len(xs)
for step in range(10000):
    idx = torch.randint(0, n, (128,))
    xb = xs[idx].unsqueeze(-1).float()
    vb = vs[idx].unsqueeze(-1).float()
    Fb = Fs[idx].unsqueeze(-1).float()
    opt.zero_grad()
    pred = model.force(xb, vb)
    loss = loss_fn(pred, Fb)
    loss.backward()
    opt.step()
    if step % 2000 == 0 or step == 9999:
        print(f"  [with_vel] step {step:5d}  loss {loss.item():.6f}")

# Evaluate
model.eval()
with torch.no_grad():
    xh, vh, Fh = langevin_traj(ho_world, 500, seed=42)
    xh_t = xh.unsqueeze(-1).float()
    vh_t = vh.unsqueeze(-1).float()
    pred_F = model.force(xh_t, vh_t).squeeze(-1)
    fm = (pred_F - Fh.float()).abs().mean().item()
    print(f"\n  DirectWithVelocity: force_MAE={fm:.4f}")

# Rollout
x = torch.tensor(-0.9, dtype=torch.float32)
v = torch.tensor(0.5, dtype=torch.float32)
pred_xs = [x.clone()]
torch.manual_seed(43)
for _ in range(499):
    xt = x.unsqueeze(0).unsqueeze(-1)
    vt = v.unsqueeze(0).unsqueeze(-1)
    F = model.force(xt, vt).item()
    v = v + (F - ho_world.gamma * v) * 0.01 + (2*ho_world.gamma*ho_world.kT)**0.5 * (0.01**0.5) * torch.randn(1).item()
    x = x + v * 0.01
    pred_xs.append(x.clone())
pred_traj = torch.stack(pred_xs)
ref_traj = xh[:500].float()
drift = (pred_traj - ref_traj).abs().mean().item() / (ref_traj.max() - ref_traj.min()).item()
print(f"  DirectWithVelocity: rollout_drift={drift:.4f}")
