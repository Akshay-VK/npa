"""G3 molecular energy models on pairwise H-H distances.

Three atoms give three pairwise distances, so rotation and translation
invariance are exact by construction. Two models:

- ``mlp``: a plain MLP on the three distances. The simplest baseline.
- ``pairwise``: a learnable Morse pair potential plus a gated three-body MLP.
  The Morse part fixes the dissociation limit (pairs go to zero when far
  apart); the gated three-body term carries the barrier, which is a
  three-body effect that a pairwise sum cannot represent.

Energies are in kcal/mol, relative to the reactant at the training level.
"""

from __future__ import annotations

import torch
import torch.nn as nn

KDIST = 1.5  # distance scale, Angstrom


def pairwise_distances(x: torch.Tensor) -> torch.Tensor:
    """x: (B, 3, 3) -> (B, 3) distances for pairs (0,1), (0,2), (1,2)."""
    i = torch.tensor([0, 0, 1], device=x.device)
    j = torch.tensor([1, 2, 2], device=x.device)
    return (x[:, i] - x[:, j]).norm(dim=-1).clamp(min=1e-6)


def _mlp(in_dim: int, hidden: int, out_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(in_dim, hidden), nn.Tanh(),
        nn.Linear(hidden, hidden), nn.Tanh(),
        nn.Linear(hidden, out_dim),
    )


class MolecularEnergy(nn.Module):
    """Plain distance MLP: energy is an arbitrary smooth function of distances."""

    def __init__(self, hidden: int = 64):
        super().__init__()
        self.net = _mlp(3, hidden, 1)
        self.offset = nn.Parameter(torch.zeros(1))

    def energy_from_distances(self, d: torch.Tensor) -> torch.Tensor:
        inp = (d - KDIST) / KDIST
        return self.net(inp).squeeze(-1) + self.offset

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.energy_from_distances(pairwise_distances(x))

    def force(self, x: torch.Tensor) -> torch.Tensor:
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            e = self.forward(x).sum()
            g, = torch.autograd.grad(e, x, create_graph=True)
        return -g


class PairwiseMolecularEnergy(nn.Module):
    """Morse pairs plus a gated three-body correction."""

    def __init__(self, hidden: int = 32, gate_scale: float = 3.0):
        super().__init__()
        # Morse: E = D * (1 - exp(-a (r - r0)))^2 - D, one well per pair.
        self.log_d = nn.Parameter(torch.log(torch.tensor(109.5)))   # kcal/mol
        self.log_a = nn.Parameter(torch.log(torch.tensor(1.94)))    # 1/Angstrom
        self.r0 = nn.Parameter(torch.tensor(0.74))                  # Angstrom
        self.three = _mlp(3, hidden, 1)
        self.offset = nn.Parameter(torch.zeros(1))
        self.gate_scale = gate_scale

    def pair_energy(self, d: torch.Tensor) -> torch.Tensor:
        d_scale = torch.exp(self.log_d)
        a = torch.exp(self.log_a).clamp(max=8.0)
        return d_scale * (1.0 - torch.exp(-a * (d - self.r0))) ** 2 - d_scale

    def energy_from_distances(self, d: torch.Tensor) -> torch.Tensor:
        e2 = self.pair_energy(d).sum(-1)
        # Three-body term vanishes when the largest distance is large, so the
        # dissociation limit is set by the Morse pairs alone.
        gate = torch.exp(-(d.max(dim=-1).values / self.gate_scale) ** 4)
        e3 = self.three((d - KDIST) / KDIST).squeeze(-1) * gate
        return e2 + e3 + self.offset

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.energy_from_distances(pairwise_distances(x))

    def force(self, x: torch.Tensor) -> torch.Tensor:
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            e = self.forward(x).sum()
            g, = torch.autograd.grad(e, x, create_graph=True)
        return -g


def build_molecular(kind: str = "pairwise", hidden: int = 64,
                    gate_scale: float = 3.0) -> nn.Module:
    if kind == "mlp":
        return MolecularEnergy(hidden=hidden)
    if kind == "pairwise":
        return PairwiseMolecularEnergy(hidden=max(hidden // 2, 8),
                                       gate_scale=gate_scale)
    raise ValueError(f"unknown molecular model: {kind}")
