"""npa: energy-based Neural Particle Automata for molecular dynamics.

Deep modules live here. The interfaces are small; the implementations are deep.
See docs/03-method-design for the architecture decisions behind each variant.
"""

from .core.sim import DirectDynamics, EnergyModel  # noqa: F401

__version__ = "0.0.0"