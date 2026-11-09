"""Model variants. Each is a deep module behind DirectDynamics or EnergyModel."""

from __future__ import annotations


class DynamicsBase:
    """Common bookkeeping (eps0, alpha, state_dims) shared by all variants."""

    state_dims: int = 16
    hidden_dims: int = 128