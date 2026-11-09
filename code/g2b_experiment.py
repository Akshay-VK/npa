"""G2b: non-conservative dynamics (Langevin). Force = -dU/dx - gamma*v.

V2 (stateless): MLP(x) -> F. Can only learn -dU/dx (misses friction).
V3b (stateful): MLP(x, h) -> F, h' = g(x, v, h). Can learn full force.
Ablation: V3b with h=0 (should equal V2).

This is the cleanest test of "does state help": V2 fails by construction
(cannot represent velocity-dependent force), V3b can.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F


# --- Worlds ---

@dataclass
class DampedWorld:
    """Double well with Langevin dynamics. Force = -dU/dx - gamma*v."""
    barrier: float = 1.0
    gamma: float = 0.5
    kT: float = 0.1
    seed: int = 0
    held_out: bool = False

    def __post_init__(self):
        if self.held_out:
            self.barrier = 1.3
            self.gamma = 0.6

    def potential(self, x):
        return self.barrier * (x ** 2 - 1.0) ** 2

    def force_conservative(self, x):
        return -self.barrier * 4.0 * x * (x ** 2 - 1.0)

    def force_total(self, x, v):
        return self.force_conservative(x) - self.gamma * v


def make_damped_world(held_out=False, seed=0):
    return DampedWorld(held_out=held_out, seed=seed)


def langevin_traj(world, n_steps, dt=0.01, seed=0):
    """Generate (x, v, F_total) from Langevin dynamics."""
    torch.manual_seed(seed)
    x = torch.tensor(world.x0 if hasattr(world, "x0") else -0.9, dtype=torch.float64)
    v = torch.tensor(0.5, dtype=torch.float64)
    xs, vs, Fs = [], [], []
    sqrt_2gkT = (2.0 * world.gamma * world.kT) ** 0.5
    for _ in range(n_steps):
        xs.append(x.clone())
        vs.append(v.clone())
        F = world.force_total(x, v)
        Fs.append(F.clone())
        v = v + (world.force_conservative(x) - world.gamma * v) * dt + sqrt_2gkT * (dt ** 0.5) * torch.randn(1).item()
        x = x + v * dt
    return torch.stack(xs), torch.stack(vs), torch.stack(Fs)


# --- Models ---

class DirectStateless(nn.Module):
    """V2-style: MLP(x) -> F. Cannot see velocity. Cannot learn friction."""

    def __init__(self, hidden=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )

    def force(self, x):
        return self.net(x)

    def forward(self, x, h=None):
        return self.net(x)


class DirectStateful(nn.Module):
    """V3b-style: MLP(x, h) -> F, h' = g(x, v, h). Can encode velocity."""

    def __init__(self, hidden=64, latent=16):
        super().__init__()
        self.latent = latent
        self.force_net = nn.Sequential(
            nn.Linear(1 + latent, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )
        self.state_net = nn.Sequential(
            nn.Linear(1 + 1 + latent, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, latent),
        )

    def force(self, x, h):
        return self.force_net(torch.cat([x, h], dim=-1))

    def step_state(self, x, v, h):
        inp = torch.cat([x, v, h], dim=-1)
        return h + self.state_net(inp)  # residual

    def forward(self, x, h=None):
        if h is None:
            h = torch.zeros(x.shape[0], self.latent, device=x.device, dtype=x.dtype)
        return self.force_net(torch.cat([x, h], dim=-1))


# --- Training ---

def train_stateless(world, steps=10000, lr=1e-3, batch=128, seed=0):
    torch.manual_seed(seed)
    xs, vs, Fs = langevin_traj(world, 5000, seed=seed)
    # Train on conservative force only (stateless can't see velocity)
    F_conservative = torch.stack([world.force_conservative(x) for x in xs])
    model = DirectStateless(hidden=64)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    n = len(xs)
    for step in range(steps):
        idx = torch.randint(0, n, (batch,))
        xb = xs[idx].unsqueeze(-1).float()
        Fb = F_conservative[idx].unsqueeze(-1).float()
        opt.zero_grad()
        pred = model.force(xb)
        loss = loss_fn(pred, Fb)
        loss.backward()
        opt.step()
        if step % 2000 == 0 or step == steps - 1:
            print(f"  [stateless] step {step:5d}  loss {loss.item():.6f}")
    return model


def train_stateful(world, steps=10000, lr=1e-3, n_traj=5, traj_len=1000, seed=0):
    torch.manual_seed(seed)
    model = DirectStateful(hidden=64, latent=16)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    # Teacher-forced training: compute h from (x, v) at each step independently.
    # No sequential dependency during training. State is evolved at eval time.
    xs_all, vs_all, Fs_all = [], [], []
    for ti in range(n_traj):
        xs, vs, Fs = langevin_traj(world, traj_len, seed=seed + ti)
        xs_all.append(xs); vs_all.append(vs); Fs_all.append(Fs)
    xs_all = torch.cat(xs_all); vs_all = torch.cat(vs_all); Fs_all = torch.cat(Fs_all)
    n = len(xs_all)
    batch = 128
    for step in range(steps):
        idx = torch.randint(0, n, (batch,))
        xb = xs_all[idx].unsqueeze(-1).float()
        vb = vs_all[idx].unsqueeze(-1).float()
        Fb = Fs_all[idx].unsqueeze(-1).float()
        opt.zero_grad()
        h = torch.zeros(batch, model.latent)
        h = model.step_state(xb, vb, h)
        pred_F = model.force(xb, h)
        loss = loss_fn(pred_F, Fb)
        loss.backward()
        opt.step()
        if step % 2000 == 0 or step == steps - 1:
            print(f"  [stateful]  step {step:5d}  loss {loss.item():.6f}")
    return model


def evaluate(model, world, n_steps=500, seed=42, is_stateful=False):
    """Evaluate force MAE and rollout drift on held-out data."""
    xs, vs, Fs = langevin_traj(world, n_steps, seed=seed)
    model.eval()
    with torch.no_grad():
        if is_stateful:
            h = torch.zeros(model.latent)
            preds = []
            for t in range(n_steps):
                xt = xs[t].unsqueeze(0).unsqueeze(-1).float()
                vt = vs[t].unsqueeze(0).unsqueeze(-1).float()
                preds.append(model.force(xt, h.unsqueeze(0)).item())
                h = model.step_state(xt, vt, h.unsqueeze(0)).squeeze(0)
            pred_F = torch.tensor(preds)
        else:
            pred_F = model.force(xs.unsqueeze(-1).float()).squeeze(-1)
        force_mae = (pred_F - Fs.float()).abs().mean().item()

        # Rollout
        x = torch.tensor(world.x0 if hasattr(world, "x0") else -0.9, dtype=torch.float32)
        v = torch.tensor(0.5, dtype=torch.float32)
        h = torch.zeros(model.latent) if is_stateful else None
        pred_xs = [x.clone()]
        sqrt_2gkT = (2.0 * world.gamma * world.kT) ** 0.5
        torch.manual_seed(seed + 100)
        for _ in range(n_steps - 1):
            xt = x.unsqueeze(0).unsqueeze(-1)
            vt = v.unsqueeze(0).unsqueeze(-1)
            if is_stateful:
                F = model.force(xt, h.unsqueeze(0)).item()
                h = model.step_state(xt, vt, h.unsqueeze(0)).squeeze(0).detach()
            else:
                F = model.force(xt).item()
            v = v + (F - world.gamma * v) * 0.01 + sqrt_2gkT * (0.01 ** 0.5) * torch.randn(1).item()
            x = x + v * 0.01
            pred_xs.append(x.clone())
        pred_traj = torch.stack(pred_xs)
        ref_traj = xs[:n_steps].float()
        drift = (pred_traj - ref_traj).abs().mean().item() / (ref_traj.max() - ref_traj.min()).item()
    return force_mae, drift


def run_ablation(world, steps=10000, seed=0):
    """V3b with state frozen to zeros (should equal V2)."""
    torch.manual_seed(seed)
    model = DirectStateful(hidden=64, latent=16)
    # Freeze state: always pass zeros
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    xs, vs, Fs = langevin_traj(world, 5000, seed=seed)
    F_conservative = torch.stack([world.force_conservative(x) for x in xs])
    n = len(xs)
    for step in range(steps):
        idx = torch.randint(0, n, (128,))
        xb = xs[idx].unsqueeze(-1).float()
        Fb = F_conservative[idx].unsqueeze(-1).float()
        opt.zero_grad()
        # State frozen to zero
        h = torch.zeros(128, 16)
        pred = model.force(xb, h)
        loss = loss_fn(pred, Fb)
        loss.backward()
        opt.step()
        if step % 2000 == 0 or step == steps - 1:
            print(f"  [ablation] step {step:5d}  loss {loss.item():.6f}")
    return model
# --- Main experiment runner ---

if __name__ == "__main__":
    import time, json, os

    print("=" * 60)
    print("G2b: Non-conservative dynamics (Langevin friction)")
    print("=" * 60)

    world = make_damped_world(held_out=False, seed=0)
    ho_world = make_damped_world(held_out=True, seed=0)

    print(f"\nWorld: barrier={world.barrier}, gamma={world.gamma}, kT={world.kT}")
    print(f"Held-out: barrier={ho_world.barrier}, gamma={ho_world.gamma}")

    print("\n--- Training V2 (stateless, position-only) ---")
    t0 = time.time()
    model_v2 = train_stateless(world, steps=10000, lr=1e-3, seed=0)
    print(f"  time: {time.time()-t0:.1f}s")

    print("\n--- Training V3b (stateful, encodes velocity) ---")
    t0 = time.time()
    model_v3b = train_stateful(world, steps=10000, lr=1e-3, seed=0)
    print(f"  time: {time.time()-t0:.1f}s")

    print("\n--- Ablation: V3b with state frozen to zero ---")
    t0 = time.time()
    model_abl = run_ablation(world, steps=10000, seed=0)
    print(f"  time: {time.time()-t0:.1f}s")

    print("\n" + "=" * 60)
    print("EVALUATION (held-out world)")
    print("=" * 60)

    fm_v2, drift_v2 = evaluate(model_v2, ho_world, n_steps=500, seed=42, is_stateful=False)
    fm_v3b, drift_v3b = evaluate(model_v3b, ho_world, n_steps=500, seed=42, is_stateful=True)
    fm_abl, drift_abl = evaluate(model_abl, ho_world, n_steps=500, seed=42, is_stateful=True)

    print(f"\n  V2 (stateless):     force_MAE={fm_v2:.4f}  rollout_drift={drift_v2:.4f}")
    print(f"  V3b (stateful):     force_MAE={fm_v3b:.4f}  rollout_drift={drift_v3b:.4f}")
    print(f"  Ablation (frozen):  force_MAE={fm_abl:.4f}  rollout_drift={drift_abl:.4f}")

    print("\n" + "=" * 60)
    print("VERDICT")
    print("=" * 60)
    if fm_v3b < fm_v2 * 0.9:
        print("  State HELPS: V3b beats V2 by >10% on force MAE.")
    elif fm_v3b < fm_v2:
        print("  State helps marginally: V3b slightly better than V2.")
    else:
        print("  State does NOT help: V2 matches or beats V3b.")
    if abs(fm_abl - fm_v2) < 0.01:
        print("  Ablation confirms: frozen state ~ V2 (state is doing the work).")
    else:
        print("  Ablation inconclusive: frozen state differs from V2.")

    os.makedirs("runs/g2b", exist_ok=True)
    results = {
        "world": {"barrier": world.barrier, "gamma": world.gamma, "kT": world.kT},
        "held_out": {"barrier": ho_world.barrier, "gamma": ho_world.gamma},
        "v2_stateless": {"force_mae": fm_v2, "rollout_drift": drift_v2},
        "v3b_stateful": {"force_mae": fm_v3b, "rollout_drift": drift_v3b},
        "ablation_frozen": {"force_mae": fm_abl, "rollout_drift": drift_abl},
    }
    with open("runs/g2b/results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to runs/g2b/results.json")

# --- Bonus: stateless model with velocity input (control for V3b) ---
class DirectWithVelocity(nn.Module):
    """MLP(x, v) -> F. Stateless but velocity-aware. Control for V3b."""
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
    def forward(self, x, v=None):
        if v is None:
            v = torch.zeros_like(x)
        return self.net(torch.cat([x, v], dim=-1))

def train_with_velocity(world, steps=10000, lr=1e-3, seed=0):
    torch.manual_seed(seed)
    xs, vs, Fs = langevin_traj(world, 5000, seed=seed)
    model = DirectWithVelocity(hidden=64)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    n = len(xs)
    for step in range(steps):
        idx = torch.randint(0, n, (128,))
        xb = xs[idx].unsqueeze(-1).float()
        vb = vs[idx].unsqueeze(-1).float()
        Fb = Fs[idx].unsqueeze(-1).float()
        opt.zero_grad()
        pred = model.force(xb, vb)
        loss = loss_fn(pred, Fb)
        loss.backward()
        opt.step()
        if step % 2000 == 0 or step == steps - 1:
            print(f"  [with_vel] step {step:5d}  loss {loss.item():.6f}")
    return model

if __name__ == "__main__":
    pass  # already have main block above
