"""V2: stateless energy model. Force = -dE/dx via autograd."""

from __future__ import annotations

import torch
import torch.nn as nn


class EnergyModel(nn.Module):
    """MLP(x) -> E. Force derived by autograd. Standard MLIP-style."""

    def __init__(self, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )

    def energy(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def force(self, x: torch.Tensor) -> torch.Tensor:
        x = x.clone().requires_grad_(True)
        E = self.net(x)
        F = -torch.autograd.grad(E.sum(), x, create_graph=True)[0]
        return F.detach()

    def step(self, x: torch.Tensor, v: torch.Tensor, dt: float) -> tuple[torch.Tensor, torch.Tensor]:
        F = self.force(x)
        v = v + F.squeeze(-1) * dt
        x = x + v * dt
        return x, v