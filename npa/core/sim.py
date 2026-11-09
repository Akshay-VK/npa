"""The stepper: the one deep module everything else depends on.

Models implement DirectDynamics or EnergyModel. The trainer and evaluator only
ever call `step` and `energy`, so a new variant is a new module, not a new
pipeline.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable, Tuple

import torch


@runtime_checkable
class DirectDynamics(Protocol):
    """Predicts the update directly (V1, NPA-faithful)."""

    def forward(self, x: torch.Tensor, s: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]: ...


@runtime_checkable
class EnergyModel(Protocol):
    """Predicts a scalar energy (V2, V3a, V3b). Force is -dE/dx."""

    def energy(self, x: torch.Tensor, s: torch.Tensor) -> torch.Tensor: ...


def step_direct(model: DirectDynamics, x, s, grid, dt: float = 1.0):
    """One Euler step for a direct model. Detachment rules live here, once."""
    raise NotImplementedError("v0.0")


def step_energy(model: EnergyModel, x, s, grid, dt: float = 1.0):
    """One Euler step from an energy: x' = x - dt * dE/dx, s' = s + ..."""
    raise NotImplementedError("v0.0")