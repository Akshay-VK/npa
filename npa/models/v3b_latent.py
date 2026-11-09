"""V3b: energy model with persistent latent state.

State update now takes velocity, so the latent state can encode damping/memory.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class LatentEnergyModel(nn.Module):
    """MLP(x, h) -> E, h' = g(x, v, h). State carries memory across steps."""

    def __init__(self, hidden: int = 32, latent: int = 8):
        super().__init__()
        self.latent = latent
        self.energy_net = nn.Sequential(
            nn.Linear(1 + latent, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )
        self.state_net = nn.Sequential(
            nn.Linear(1 + 1 + latent, hidden), nn.Tanh(),  # x, v, h
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, latent),
        )

    def energy(self, x: torch.Tensor, h: torch.Tensor) -> torch.Tensor:
        inp = torch.cat([x, h], dim=-1)
        return self.energy_net(inp)

    def force(self, x: torch.Tensor, h: torch.Tensor) -> torch.Tensor:
        x = x.clone().requires_grad_(True)
        E = self.energy_net(torch.cat([x, h.detach()], dim=-1))
        F = -torch.autograd.grad(E.sum(), x, create_graph=True)[0]
        return F.detach()

    def step_state(self, x: torch.Tensor, v: torch.Tensor, h: torch.Tensor) -> torch.Tensor:
        inp = torch.cat([x, v, h], dim=-1)
        return self.state_net(inp)

    def step(self, x: torch.Tensor, v: torch.Tensor, h: torch.Tensor, dt: float):
        F = self.force(x, h)
        h_new = self.step_state(x, v, h)
        v = v + F.squeeze(-1) * dt
        x = x + v * dt
        return x, v, h_new