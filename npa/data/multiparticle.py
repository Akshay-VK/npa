"""Multi-particle worlds for G2c.

N particles in a 2D harmonic well with pairwise spring interactions.
Deterministic trajectories via velocity Verlet. Held-out variant changes
spring stiffness and well strength.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch


@dataclass
class MultiParticleWorld:
    """N particles in 2D harmonic well with pairwise springs."""
    n: int
    dim: int = 2
    k_well: float = 1.0       # harmonic well strength
    k_spring: float = 0.5     # pairwise spring stiffness
    spring_cutoff: float = 1.0  # spring interaction cutoff
    seed: int = 0
    held_out: bool = False

    def __post_init__(self):
        if self.held_out:
            self.k_well = 1.3
            self.k_spring = 0.7
        torch.manual_seed(self.seed)
        # Random initial positions in [-1, 1]^dim
        self.x0 = (torch.rand(self.n, self.dim) * 2 - 1) * 0.5
        self.v0 = torch.randn(self.n, self.dim) * 0.1

    def energy(self, x: torch.Tensor, v: torch.Tensor = None) -> torch.Tensor:
        """Total energy: well + springs + kinetic."""
        # Well energy
        E_well = 0.5 * self.k_well * (x ** 2).sum()
        # Spring energy (pairwise, within cutoff)
        E_spring = 0.0
        for i in range(self.n):
            for j in range(i + 1, self.n):
                r = (x[i] - x[j]).norm()
                if r < self.spring_cutoff:
                    E_spring = E_spring + 0.5 * self.k_spring * (r - 0.5) ** 2
        E = E_well + E_spring
        if v is not None:
            E = E + 0.5 * (v ** 2).sum()
        return E

    def force(self, x: torch.Tensor) -> torch.Tensor:
        """Force on each particle: -dE/dx."""
        F = -self.k_well * x.clone()  # well force
        # Spring forces
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    continue
                r_vec = x[j] - x[i]
                r = r_vec.norm()
                if r < self.spring_cutoff and r > 1e-6:
                    F[i] = F[i] + self.k_spring * (r - 0.5) * r_vec / r
        return F

    def trajectory(self, n_steps: int, dt: float = 0.01) -> tuple[torch.Tensor, torch.Tensor]:
        """Velocity Verlet integration. Returns (positions, velocities) of shape (n_steps, N, dim)."""
        x = self.x0.clone().double()
        v = self.v0.clone().double()
        xs, vs = [], []
        for _ in range(n_steps):
            xs.append(x.clone())
            vs.append(v.clone())
            F = self.force(x)
            v = v + 0.5 * F * dt
            x = x + v * dt
            F_new = self.force(x)
            v = v + 0.5 * F_new * dt
        return torch.stack(xs), torch.stack(vs)


def make_world(n: int = 64, held_out: bool = False, seed: int = 0) -> MultiParticleWorld:
    return MultiParticleWorld(n=n, held_out=held_out, seed=seed)


def energy_drift(world, traj_xs, traj_vs=None, dt=0.01) -> float:
    """Compute relative energy drift over a trajectory."""
    if traj_vs is not None:
        energies = [world.energy(x, v).item() for x, v in zip(traj_xs, traj_vs)]
    else:
        energies = [world.energy(x).item() for x in traj_xs]
    E0 = energies[0]
    if abs(E0) < 1e-8:
        return float("inf")
    drift = max(abs(e - E0) for e in energies) / abs(E0)
    return drift