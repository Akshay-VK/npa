"""CPU/brute-force replacement for the NPA `sphops` CUDA package.

The official repo only ships CUDA kernels. This module exposes the exact same
import surface (`HashGrid`, `bin_particles`, `density`, `blur`, `gradient`,
`density_gradient`, `moment_matrix`, `gradient_hybrid`) backed by the
`torch_sph.py` reference implementation the authors use for correctness tests.

Cost is O(B*N^2) memory and time per operator. Fine for G0 at N <= ~1024;
N = 4096 forward-only is borderline (the feature-gradient tensor is ~2 GB).

Usage:
    import npa_bruteforce
    npa_bruteforce.install()      # must run before importing models.npa
"""

import os
import sys
import types

import torch

NPA_DIR = os.environ.get(
    "NPA_DIR", os.path.expanduser("~/npa-work/vendor/NPA")
)

_sph_dir = os.path.join(NPA_DIR, "sphops")
if _sph_dir not in sys.path:
    sys.path.insert(0, _sph_dir)

import torch_sph as _ts  # noqa: E402  (path set above)


class _Snapshot:
    """Stand-in for the CUDA hash-grid snapshot. Brute force needs no bins."""

    __slots__ = ("dim", "eps", "grid", "permutation", "bin_offsets", "block_info")

    def __init__(self, dim, eps):
        self.dim = dim
        self.eps = eps
        self.grid = None
        self.permutation = None
        self.bin_offsets = None
        self.block_info = None


class HashGrid:
    """Same constructor signature as the CUDA class; no binning happens."""

    def __init__(
        self,
        dim=2,
        boundary="periodic",
        mode="grid",
        grid_size=(16, 16),
        eps=0.1,
        num_particles=4096,
        batch_size=8,
        max_particles_per_block=64,
        **kwargs,
    ):
        self.dim = dim
        self.boundary = boundary
        self.mode = mode
        self.grid_size = tuple(grid_size)
        self.eps = eps
        self.num_particles = num_particles
        self.batch_size = batch_size
        self.max_particles_per_block = max_particles_per_block
        self.max_blocks = 0
        self.device = torch.device("cpu")

    def instantiate(self, x):
        return _Snapshot(self.dim, self.eps)

    def wrap_positions(self, x):
        # `clamped` is the identity in the reference implementation too.
        return x


def bin_particles(x, s, snapshot, mass=None):
    if mass is None:
        return x, s
    return x, s, mass


def unbin_particles(x_bin, s_bin, snapshot, mass_bin=None):
    if mass_bin is None:
        return x_bin, s_bin
    return x_bin, s_bin, mass_bin


def density(x, snapshot, mass=None):
    return _ts.density(x, snapshot.eps, mass=mass)


def blur(x, rho, s, snapshot, mass=None):
    return _ts.blur(x, rho, s, snapshot.eps, mass=mass)


def gradient(x, rho, s, snapshot, mass=None):
    return _ts.gradient(x, rho, s, snapshot.eps, mass=mass)


def density_gradient(x, snapshot, mass=None):
    return _ts.density_gradient(x, snapshot.eps, mass=mass)


def moment_matrix(x, rho, snapshot, mass=None):
    return _ts.moment_matrix(x, rho, snapshot.eps, mass=mass)


def gradient_hybrid(x, rho, s, snapshot, mass=None):
    """Matches sphops.sph.gradient_hybrid: raw gradient plus detached correction."""
    with torch.no_grad():
        M = moment_matrix(x, rho, snapshot, mass=mass)
        L = torch.linalg.pinv(M, hermitian=True, rtol=1e-3)
    raw = gradient(x, rho, s, snapshot, mass=mass)
    return raw + (raw @ L - raw).detach()


def count(x, snapshot, mass=None):
    return _ts.count(x, snapshot.eps)


_PUBLIC = (
    "HashGrid",
    "bin_particles",
    "unbin_particles",
    "density",
    "blur",
    "gradient",
    "density_gradient",
    "moment_matrix",
    "gradient_hybrid",
    "count",
)


def install():
    """Install this module as `sphops` in sys.modules."""
    mod = types.ModuleType("sphops")
    for name in _PUBLIC:
        setattr(mod, name, globals()[name])
    mod.torch_sph = _ts
    sys.modules["sphops"] = mod
    sys.modules["sphops.sph"] = mod
    sys.modules["sphops.torch_sph"] = _ts
    # `sphops/utils.py` would otherwise shadow the repo's `utils/` package.
    while _sph_dir in sys.path:
        sys.path.remove(_sph_dir)
    if NPA_DIR in sys.path:
        sys.path.remove(NPA_DIR)
    sys.path.insert(0, NPA_DIR)
    return mod
