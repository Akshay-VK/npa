"""V3b: energy model with persistent latent state — single network (NCA-style).

One network takes (x, state) and outputs (E, delta_state). The hidden state
channels are part of the state vector, not a separate network. Meaning is
emergent, not pre-assigned — this is how NCA/NPA actually work.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class LatentEnergyModel(nn.Module):
    """Single MLP: (x, state) -> (E, delta_state). NCA-style."""

    def __init__(self, hidden: int = 32, latent: int = 8):
        super().__init__()
        self.latent = latent  # kept for training-loop compatibility
        self.state_dim = latent
        # single network outputs energy + state update
        self.net = nn.Sequential(
            nn.Linear(1 + latent, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1 + latent),
        )

    def forward(self, x: torch.Tensor, s: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        inp = torch.cat([x, s], dim=-1)
        out = self.net(inp)
        E = out[..., 0:1]
        ds = out[..., 1:]
        return E, ds

    def energy(self, x: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        E, _ = self.forward(x, s)
        return E

    def force(self, x: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        x = x.clone().requires_grad_(True)
        s_det = s.detach()
        inp = torch.cat([x, s_det], dim=-1)
        out = self.net(inp)
        E = out[..., 0:1]
        F = -torch.autograd.grad(E.sum(), x, create_graph=True)[0]
        return F.detach()

    def step_state(self, x: torch.Tensor, v: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        # v is accepted for interface compatibility but state update uses (x, s)
        _, ds = self.forward(x, s)
        return s + ds  # residual update, like NCA

    def step(self, x: torch.Tensor, v: torch.Tensor, s: torch.Tensor, dt: float):
        F = self.force(x, s)
        s_new = self.step_state(x, v, s)
        v = v + F.squeeze(-1) * dt
        x = x + v * dt
        return x, v, s_new