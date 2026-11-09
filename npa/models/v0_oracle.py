"""V0: analytic oracle. Ground truth that ML variants must recover."""

from __future__ import annotations

import torch
import torch.nn as nn


class HarmonicOracle:
    """F = -k*x, E = 0.5*k*x^2. Exact, no parameters."""

    def __init__(self, k: float = 1.0):
        self.k = k

    def energy(self, x: torch.Tensor) -> torch.Tensor:
        return 0.5 * self.k * x ** 2

    def force(self, x: torch.Tensor) -> torch.Tensor:
        return -self.k * x