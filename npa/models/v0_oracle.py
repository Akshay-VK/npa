"""V0: analytic oracle. The ground truth the ML variants must recover.

Deep module: a known force field (harmonic + double well) with an exact energy.
Tests use it as the reference; v0.2/v0.3 train against it.
"""

from __future__ import annotations

import torch

from npa.models.base import DynamicsBase


class HarmonicOracle(DynamicsBase):
    """F = -k (x - x0), E = 0.5 k |x - x0|^2. The sanity check for the loop."""

    def __init__(self, k: float = 1.0):
        self.k = k

    def energy(self, x: torch.Tensor, s: torch.Tensor | None = None) -> torch.Tensor:
        raise NotImplementedError("v0.0")

    def force(self, x: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("v0.0")