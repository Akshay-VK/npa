"""G2e additions: stateless history, EMA state, residual energy, combined.

These are new arms for the G2e experiment. They reuse the shared perception
from ``mp_perception`` and the same interface (``force``, ``step``,
``force_and_ds``) as the G2d arms so the training/eval code can treat them
uniformly.
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


class MPHistoryEnergy(nn.Module):
    """V2H: stateless energy conditioned on a fixed window of past positions.

    The history is a buffer of the last ``k`` observed positions per particle,
    stored relative to the current position. It is not a learned state: it is
    the raw observation window. The model is a fair stateless baseline with
    explicit memory, so that the latent-state arm can be compared against the
    strongest non-state model.
    """

    def __init__(self, dim: int = 2, hidden: int = 64, cutoff: float = 1.0,
                 history: int = 4):
        super().__init__()
        self.dim = dim
        self.history = history
        self.cutoff = cutoff
        in_dim = dim + (dim + 1) + history * dim
        self.net = _mlp(in_dim, hidden, 1)

    def _features(self, x: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        agg, rho = neighbour_features(x, self.cutoff)
        # s: (B, N, k, D) history of past positions relative to current.
        s_rel = s.reshape(s.shape[0], s.shape[1], -1)
        return torch.cat([x, agg, rho, s_rel], dim=-1)

    def energy(self, x: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        inp = self._features(x, s)
        return self.net(inp).sum(dim=1)

    def force(self, x: torch.Tensor, s: torch.Tensor | None = None) -> torch.Tensor:
        if s is None:
            s = torch.zeros(x.shape[0], x.shape[1], self.history, self.dim,
                            device=x.device, dtype=x.dtype)
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            E = self.energy(x, s)
            g = torch.autograd.grad(E.sum(), x, create_graph=True, retain_graph=True)[0]
        return -g

    def force_and_ds(self, x: torch.Tensor, s: torch.Tensor):
        F = self.force(x, s)
        # Update the history buffer: drop the oldest, append the current x.
        B, N, k, D = s.shape
        new_s = torch.cat([s[:, :, 1:, :], x.detach().unsqueeze(2)], dim=2)
        return F, new_s - s  # delta form, consistent with the other arms

    def step(self, x, s, dt: float = 0.01):
        F, ds = self.force_and_ds(x, s)
        s_new = s + ds
        return x + F * dt, s_new, F


class MPEMAEnergy(nn.Module):
    """V3b with an EMA (observation-integrated) state update.

    The state is a low-pass filter of the observed features, which is more
    stable than a free additive delta and integrates information over time.
    """

    def __init__(self, dim: int = 2, hidden: int = 64, state_dim: int = 4,
                 cutoff: float = 1.0, state_scale: float = 0.1):
        super().__init__()
        self.dim = dim
        self.state_dim = state_dim
        self.cutoff = cutoff
        self.state_scale = state_scale
        self.net = _mlp(2 * dim + 1 + state_dim, hidden, 1 + state_dim)
        # Learned gate per state dimension, initialised near 0.5.
        self.gate = nn.Parameter(torch.zeros(state_dim))

    def _gate(self) -> torch.Tensor:
        return torch.sigmoid(self.gate)

    def forward(self, x: torch.Tensor, s: torch.Tensor):
        agg, rho = neighbour_features(x, self.cutoff)
        inp = torch.cat([x, s, agg, rho], dim=-1)
        out = self.net(inp)
        e = out[..., :1]
        cand = self.state_scale * torch.tanh(out[..., 1:])
        return e, cand

    def energy(self, x: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        e, _ = self.forward(x, s)
        return e.sum(dim=1)

    def force_and_ds(self, x: torch.Tensor, s: torch.Tensor):
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            e, cand = self.forward(x, s)
            F = -torch.autograd.grad(e.sum(), x, create_graph=True, retain_graph=True)[0]
        beta = self._gate()
        ds = beta.view(1, 1, -1) * (cand - s)
        return F, ds

    def step(self, x, s, dt: float = 0.01):
        F, ds = self.force_and_ds(x, s)
        return x + F * dt, s + ds, F


class MPResidualLatentEnergy(nn.Module):
    """V3b where the analytic harmonic well is removed from the learning target.

    E = 0.5 * k_well * ||x||^2 + E_net(x, s).  The force is -k_well x - dE_net/dx,
    so the network only has to learn the hidden and spring forces. This is a
    toy-world diagnostic: in a real molecular system there is no harmonic well.
    """

    def __init__(self, dim: int = 2, hidden: int = 64, state_dim: int = 4,
                 cutoff: float = 1.0, state_scale: float = 0.1,
                 k_well: float = 1.0):
        super().__init__()
        self.dim = dim
        self.state_dim = state_dim
        self.cutoff = cutoff
        self.state_scale = state_scale
        self.k_well = k_well
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
        well = 0.5 * self.k_well * (x ** 2).sum(dim=(1, 2))
        return (e.sum(dim=1) + well)

    def force_and_ds(self, x: torch.Tensor, s: torch.Tensor):
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            e, ds = self.forward(x, s)
            well_force = -self.k_well * x
            net_force = -torch.autograd.grad(e.sum(), x, create_graph=True,
                                            retain_graph=True)[0]
            F = well_force + net_force
        return F, ds

    def step(self, x, s, dt: float = 0.01):
        F, ds = self.force_and_ds(x, s)
        return x + F * dt, s + ds, F


class MPCombinedLatentEnergy(nn.Module):
    """V3b-combined: EMA state update + residual well. The G2e candidate."""

    def __init__(self, dim: int = 2, hidden: int = 64, state_dim: int = 4,
                 cutoff: float = 1.0, state_scale: float = 0.1,
                 k_well: float = 1.0):
        super().__init__()
        self.dim = dim
        self.state_dim = state_dim
        self.cutoff = cutoff
        self.state_scale = state_scale
        self.k_well = k_well
        self.net = _mlp(2 * dim + 1 + state_dim, hidden, 1 + state_dim)
        self.gate = nn.Parameter(torch.zeros(state_dim))

    def _gate(self) -> torch.Tensor:
        return torch.sigmoid(self.gate)

    def forward(self, x: torch.Tensor, s: torch.Tensor):
        agg, rho = neighbour_features(x, self.cutoff)
        inp = torch.cat([x, s, agg, rho], dim=-1)
        out = self.net(inp)
        e = out[..., :1]
        cand = self.state_scale * torch.tanh(out[..., 1:])
        return e, cand

    def energy(self, x: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
        e, _ = self.forward(x, s)
        well = 0.5 * self.k_well * (x ** 2).sum(dim=(1, 2))
        return (e.sum(dim=1) + well)

    def force_and_ds(self, x: torch.Tensor, s: torch.Tensor):
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            e, cand = self.forward(x, s)
            well_force = -self.k_well * x
            net_force = -torch.autograd.grad(e.sum(), x, create_graph=True,
                                            retain_graph=True)[0]
            F = well_force + net_force
        beta = self._gate()
        ds = beta.view(1, 1, -1) * (cand - s)
        return F, ds

    def step(self, x, s, dt: float = 0.01):
        F, ds = self.force_and_ds(x, s)
        return x + F * dt, s + ds, F


def build_variant(kind: str, dim: int = 2, hidden: int = 64, state_dim: int = 4,
                  cutoff: float = 1.0, k_well: float = 1.0):
    if kind == "v2h":
        return MPHistoryEnergy(dim=dim, hidden=hidden, cutoff=cutoff, history=4)
    if kind == "v3b_ema":
        return MPEMAEnergy(dim=dim, hidden=hidden, state_dim=state_dim, cutoff=cutoff)
    if kind == "v3b_residual":
        return MPResidualLatentEnergy(dim=dim, hidden=hidden, state_dim=state_dim,
                                     cutoff=cutoff, k_well=k_well)
    if kind == "v3b_combined":
        return MPCombinedLatentEnergy(dim=dim, hidden=hidden, state_dim=state_dim,
                                     cutoff=cutoff, k_well=k_well)
    raise ValueError(f"unknown g2e variant: {kind}")
