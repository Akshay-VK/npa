"""G2d world: multi-particle system with a hidden per-particle phase.

Why this world: on conservative systems (G2, G2b, G2c) the latent state had
nothing to remember. Here each particle carries a hidden phase q_i that
advances with time and local density, and contributes a force

    F_hidden_i = amp * [cos(q_i), sin(q_i)]

The phase is not a function of the current positions, so a stateless model
cannot predict the hidden force. A model with persistent per-particle state can
infer q_i from the first few displacements and track it. This is the cleanest
test of whether latent state buys anything when memory is actually necessary.

The hidden force is conservative in x at fixed q (it is -d/dx of a linear
potential), but q evolves independently of that potential, so the full system
is non-conservative: the hidden phase does work on the particles.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class HiddenForceWorld:
    """N particles in 2D with harmonic well, springs, and a hidden phase."""

    n: int = 8
    dim: int = 2
    k_well: float = 1.0
    k_spring: float = 0.5
    r0: float = 0.5
    cutoff: float = 1.0
    amp: float = 0.6          # hidden force amplitude
    omega: float = 1.0        # base phase speed
    kappa: float = 0.5        # density coupling of the phase speed
    sigma: float = 0.25       # density kernel width
    seed: int = 0
    held_out: bool = False

    def __post_init__(self):
        if self.held_out:
            self.amp = 0.7
            self.omega = 1.1
            self.kappa = 0.4
        torch.manual_seed(self.seed)
        self.x0 = (torch.rand(self.n, self.dim) * 2 - 1) * 0.5
        self.v0 = torch.randn(self.n, self.dim) * 0.05
        self.q0 = torch.rand(self.n) * 2 * torch.pi

    # ------------------------------------------------------------------ #
    # Dynamics
    # ------------------------------------------------------------------ #
    def density(self, x: torch.Tensor) -> torch.Tensor:
        """Gaussian local density, excluding self. x: (N, dim) -> (N,)."""
        d2 = ((x[:, None, :] - x[None, :, :]) ** 2).sum(-1)
        w = torch.exp(-d2 / (2 * self.sigma ** 2))
        w = w - torch.diag_embed(torch.diagonal(w))
        return w.sum(-1)

    def force(self, x: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        """Total force on each particle. x: (N, dim), q: (N,)."""
        F = -self.k_well * x
        # Pairwise springs
        d = x[:, None, :] - x[None, :, :]          # (N, N, dim), x_i - x_j
        r = d.norm(dim=-1).clamp(min=1e-6)
        mask = (r < self.cutoff) & ~torch.eye(self.n, dtype=torch.bool)
        pair = self.k_spring * ((r - self.r0) / r).unsqueeze(-1) * d
        pair = pair * mask[..., None]
        F = F + pair.sum(1)
        # Hidden phase force
        F = F + self.amp * torch.stack([torch.cos(q), torch.sin(q)], dim=-1)
        return F

    def q_dot(self, x: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        """Phase speed: base rate plus local-density coupling."""
        return self.omega + self.kappa * self.density(x)

    def step(self, x, v, q, dt: float = 0.01):
        """One velocity-Verlet step for x, forward-Euler for q."""
        F = self.force(x, q)
        v = v + 0.5 * F * dt
        x = x + v * dt
        q = q + self.q_dot(x, q) * dt
        F_new = self.force(x, q)
        v = v + 0.5 * F_new * dt
        return x, v, q

    def trajectory(self, n_steps: int, dt: float = 0.01):
        """Return (xs, vs, qs), each with leading time dimension."""
        x = self.x0.clone()
        v = self.v0.clone()
        q = self.q0.clone()
        xs, vs, qs = [], [], []
        for _ in range(n_steps):
            xs.append(x.clone())
            vs.append(v.clone())
            qs.append(q.clone())
            x, v, q = self.step(x, v, q, dt)
        return torch.stack(xs), torch.stack(vs), torch.stack(qs)

    def potential(self, x: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        """Potential energy at fixed q (hidden phase is a linear tilt)."""
        U = 0.5 * self.k_well * (x ** 2).sum()
        d = x[:, None, :] - x[None, :, :]
        r = d.norm(dim=-1).clamp(min=1e-6)
        mask = (r < self.cutoff) & ~torch.eye(self.n, dtype=torch.bool)
        U = U + (0.5 * self.k_spring * (r - self.r0) ** 2 * mask).sum() / 2
        U = U - self.amp * (torch.cos(q) * x[:, 0] + torch.sin(q) * x[:, 1]).sum()
        return U


def make_world(n: int = 8, held_out: bool = False, seed: int = 0,
               k_spring: float = 0.5) -> HiddenForceWorld:
    return HiddenForceWorld(n=n, held_out=held_out, seed=seed, k_spring=k_spring)
