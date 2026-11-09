"""Synthetic worlds. Generated on the fly; no storage, no download.

All worlds are 1D single-particle in reduced units.

G2 world: harmonic oscillator with slowly varying spring constant k(t).
Energy E(t) = 0.5*k(t)*x^2 where k(t) = k0 + amp*sin(freq*t).
A stateless model (V2) sees only x and learns the average k.
A stateful model (V3b) can track k(t) via latent state.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch


@dataclass
class World:
    kind: str
    seed: int
    x0: float
    v0: float
    params: dict = field(default_factory=dict)

    def potential(self, x: torch.Tensor, t: float = 0.0) -> torch.Tensor:
        raise NotImplementedError

    def force_conservative(self, x: torch.Tensor, t: float = 0.0) -> torch.Tensor:
        raise NotImplementedError


class HarmonicWorld(World):
    """U = 0.5*k*x^2. k may vary with time."""

    def __init__(self, k0: float = 1.0, amp: float = 0.0, freq: float = 0.01,
                 phase: float = 0.0, seed: int = 0):
        super().__init__(kind="harmonic_tv", seed=seed, x0=1.0, v0=0.0,
                         params={"k0": k0, "amp": amp, "freq": freq, "phase": phase})
        self.k0 = k0
        self.amp = amp
        self.freq = freq
        self.phase = phase

    def k(self, t: float) -> float:
        return self.k0 + self.amp * math.sin(self.freq * t + self.phase)

    def potential(self, x, t=0.0):
        return 0.5 * self.k(t) * x ** 2

    def force_conservative(self, x, t=0.0):
        return -self.k(t) * x


def make_world(kind: str, seed: int = 0, held_out: bool = False) -> World:
    if kind == "harmonic":
        return HarmonicWorld(k0=1.0, amp=0.0, seed=seed)
    if kind == "harmonic_tv":
        if held_out:
            return HarmonicWorld(k0=1.0, amp=0.3, freq=0.15, phase=0.5, seed=seed)
        return HarmonicWorld(k0=1.0, amp=0.3, freq=0.1, phase=0.0, seed=seed)
    raise ValueError(f"unknown world: {kind}")


def harmonic_trajectory(world: World, n_steps: int, dt: float = 0.01,
                       seed: int = 0) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Integrate harmonic oscillator with time-varying k. Returns (x, v, E) arrays."""
    torch.manual_seed(seed)
    x = torch.tensor(world.x0, dtype=torch.float64)
    v = torch.tensor(world.v0, dtype=torch.float64)
    k0 = world.k0 if hasattr(world, "k0") else 1.0
    xs, vs, Es = [], [], []
    for i in range(n_steps):
        t = i * dt
        xs.append(x.clone())
        vs.append(v.clone())
        k = world.k(t) if hasattr(world, "k") else k0
        E = 0.5 * k * x ** 2
        Es.append(torch.tensor(E, dtype=torch.float64))
        F = -k * x
        v = v + F * dt
        x = x + v * dt
    return torch.stack(xs), torch.stack(vs), torch.stack(Es)