"""V1: direct propagator (NPA-faithful shape). Predicts force directly."""

from __future__ import annotations

import torch
import torch.nn as nn


class DirectPropagator(nn.Module):
    """MLP(x) -> F. No energy, no latent state. The NPA-style baseline."""

    def __init__(self, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )

    def force(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def step(self, x: torch.Tensor, v: torch.Tensor, dt: float) -> tuple[torch.Tensor, torch.Tensor]:
        F = self.force(x)
        v = v + F.squeeze(-1) * dt
        x = x + v * dt
        return x, v