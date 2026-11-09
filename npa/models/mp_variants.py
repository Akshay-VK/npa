"""G2d multi-particle variants: V1 direct, V2 stateless energy, V3b latent energy.

All variants share the same neighbour perception. The only difference is
whether a persistent per-particle state is carried and updated.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from npa.models.mp_perception import neighbour_features


def _mlp(in_dim: int, hidden: int, out_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(in_dim, hidden), nn.Tanh(),
        nn.Linear(hidden, hidden), nn.Tanh(),
        nn.Linear(hidden, out_dim),
    )


class MPDirect(nn.Module):
    """V1: direct displacement, no energy, no state."""

    def __init__(self, dim: int = 2, hidden: int = 64, cutoff: float = 1.0):
        super().__init__()
        self.dim = dim
        self.cutoff = cutoff
        self.net = _mlp(2 * dim + 1, hidden, dim)

    def force(self, x: torch.Tensor, s: torch.Tensor | None = None) -> torch.Tensor:
        agg, rho = neighbour_features(x, self.cutoff)
        inp = torch.cat([x, agg, rho], dim=-1)
        return self.net(inp)

    def step(self, x, s=None, dt: float = 0.01):
        F = self.force(x, s)
        return x + F * dt, s, F


class MPEnergy(nn.Module):
    """V2: stateless energy; force = -dE/dx via autograd."""

    def __init__(self, dim: int = 2, hidden: int = 64, cutoff: float = 1.0):
        super().__init__()
        self.dim = dim
        self.cutoff = cutoff
        self.net = _mlp(2 * dim + 1, hidden, 1)

    def energy(self, x: torch.Tensor, s: torch.Tensor | None = None) -> torch.Tensor:
        agg, rho = neighbour_features(x, self.cutoff)
        inp = torch.cat([x, agg, rho], dim=-1)
        return self.net(inp).sum(dim=1)  # (B,)

    def force(self, x: torch.Tensor, s: torch.Tensor | None = None) -> torch.Tensor:
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            E = self.energy(x, s)
            F = -torch.autograd.grad(E.sum(), x, create_graph=True, retain_graph=True)[0]
        return F

    def step(self, x, s=None, dt: float = 0.01):
        F = self.force(x, s)
        return x + F * dt, s, F


class MPLatentEnergy(nn.Module):
    """V3b: energy + persistent per-particle state, single network (NCA-style)."""

    def __init__(self, dim: int = 2, hidden: int = 64, state_dim: int = 4,
                 cutoff: float = 1.0, state_scale: float = 0.1):
        super().__init__()
        self.dim = dim
        self.state_dim = state_dim
        self.cutoff = cutoff
        self.state_scale = state_scale
        self.net = _mlp(2 * dim + 1 + state_dim, hidden, 1 + state_dim)

    def forward(self, x: torch.Tensor, s: torch.Tensor):
        agg, rho = neighbour_features(x, self.cutoff)
        inp = torch.cat([x, s, agg, rho], dim=-1)
        out = self.net(inp)
        e = out[..., :1]
        ds = self.state_scale * torch.tanh(out[..., 1:])
        return e, ds

    def energy(self, x: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        e, _ = self.forward(x, s)
        return e.sum(dim=1)

    def force_and_ds(self, x: torch.Tensor, s: torch.Tensor):
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            e, ds = self.forward(x, s)
            F = -torch.autograd.grad(e.sum(), x, create_graph=True, retain_graph=True)[0]
        return F, ds

    def step(self, x, s, dt: float = 0.01):
        F, ds = self.force_and_ds(x, s)
        return x + F * dt, s + ds, F


class MPOracleEnergy(MPEnergy):
    """V2 with the true hidden phase appended. Diagnostic ceiling, not a fair arm."""

    def __init__(self, dim: int = 2, hidden: int = 64, cutoff: float = 1.0):
        super().__init__(dim=dim, hidden=hidden, cutoff=cutoff)
        self.net = _mlp(2 * dim + 1 + 2, hidden, 1)

    def energy(self, x: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        agg, rho = neighbour_features(x, self.cutoff)
        qf = torch.stack([torch.cos(q), torch.sin(q)], dim=-1)
        inp = torch.cat([x, qf, agg, rho], dim=-1)
        return self.net(inp).sum(dim=1)


def build_variant(kind: str, dim: int = 2, hidden: int = 64, state_dim: int = 4,
                  cutoff: float = 1.0):
    if kind == "v1":
        return MPDirect(dim=dim, hidden=hidden, cutoff=cutoff)
    if kind == "v2":
        return MPEnergy(dim=dim, hidden=hidden, cutoff=cutoff)
    if kind in ("v3b", "v3b_sup"):
        return MPLatentEnergy(dim=dim, hidden=hidden, state_dim=state_dim, cutoff=cutoff)
    if kind == "oracle":
        return MPOracleEnergy(dim=dim, hidden=hidden, cutoff=cutoff)
    raise ValueError(f"unknown variant: {kind}")
