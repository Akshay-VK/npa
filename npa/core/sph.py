"""Perception: SPH operators behind a small interface.

The interface is the only thing callers and tests see. The CPU brute-force
implementation (npa.core.sph_cpu) and, later, a CUDA adapter both satisfy it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import torch


@dataclass(frozen=True)
class Snapshot:
    """Opaque handle returned by HashGrid.instantiate. Treat as a token."""
    dim: int
    eps: float


class HashGrid(Protocol):
    """Spatial binning. The implementation hides how bins are built."""

    dim: int
    eps: float

    def instantiate(self, x: torch.Tensor) -> Snapshot: ...
    def wrap_positions(self, x: torch.Tensor) -> torch.Tensor: ...


@runtime_checkable
class SphBackend(Protocol):
    """The perception operators. One small surface, large implementation."""

    def density(self, x: torch.Tensor, snap: Snapshot) -> torch.Tensor: ...
    def blur(self, x: torch.Tensor, rho: torch.Tensor, s: torch.Tensor, snap: Snapshot) -> torch.Tensor: ...
    def gradient(self, x: torch.Tensor, rho: torch.Tensor, s: torch.Tensor, snap: Snapshot) -> torch.Tensor: ...
    def density_gradient(self, x: torch.Tensor, snap: Snapshot) -> torch.Tensor: ...
    def moment_matrix(self, x: torch.Tensor, rho: torch.Tensor, snap: Snapshot) -> torch.Tensor: ...
    def gradient_hybrid(self, x: torch.Tensor, rho: torch.Tensor, s: torch.Tensor, snap: Snapshot) -> torch.Tensor: ...


def make_cpu_backend() -> SphBackend:
    """Adapter over the authors' torch_sph reference (see code/npa_bruteforce.py).

    Implemented in v0.0: wraps the brute-force kernels behind this interface.
    """
    raise NotImplementedError("v0.0: wrap code/npa_bruteforce behind SphBackend")
