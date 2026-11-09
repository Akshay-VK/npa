"""G3 reference data: collinear H + H2 -> H2 + H with PySCF.

Three hydrogen atoms on a line: A at -r1, B at 0, C at +r2. The reactant is
(r1, r2) = (3.0, 0.74) Angstrom (H far from H2); the saddle is (0.93, 0.93);
the product is (0.74, 3.0). Energies are computed at a chosen level of theory
and cached to ``runs/g3_h3/<level>.npz`` so the scan is never repeated.

The cheap level for training is CCSD(T)/cc-pVDZ; the reference is
CCSD(T)/cc-pVTZ. MP2/cc-pVTZ is a negative control: it is a cheaper method
that gets the barrier wrong, so a model trained on it should fail the gate.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

HARTREE2KCAL = 627.5094740631
REACTANT = (3.0, 0.74)
SADDLE = (0.93, 0.93)
PRODUCT = (0.74, 3.0)

# 14 values per axis: 0.74 is the H2 equilibrium bond, 0.93 the saddle, and
# 4-6 Angstrom the dissociation plateau.
GRID = (0.70, 0.74, 0.80, 0.90, 0.93, 1.00, 1.10, 1.20, 1.50,
        2.00, 2.50, 3.00, 4.00, 6.00)


def h3_positions(r1: float, r2: float) -> np.ndarray:
    """(3, 3) Cartesian geometry in Angstrom, collinear along z."""
    return np.array([[0.0, 0.0, -r1],
                     [0.0, 0.0, 0.0],
                     [0.0, 0.0, r2]], dtype=np.float64)


def _molecule(r1: float, r2: float, basis: str):
    from pyscf import gto
    return gto.M(atom=[("H", (0.0, 0.0, -r1)),
                       ("H", (0.0, 0.0, 0.0)),
                       ("H", (0.0, 0.0, r2))],
                 basis=basis, unit="Angstrom", spin=1, verbose=0)


def energy(r1: float, r2: float, level: str) -> float:
    """Total electronic energy in Hartree at the requested level."""
    from pyscf import cc, mp, scf

    if level.startswith("ccsd(t)/"):
        basis = level.split("/", 1)[1]
        mol = _molecule(r1, r2, basis)
        mf = scf.UHF(mol).run()
        mycc = cc.CCSD(mf)
        mycc.run()
        return mf.e_tot + mycc.e_corr + mycc.ccsd_t()
    if level.startswith("mp2/"):
        basis = level.split("/", 1)[1]
        mol = _molecule(r1, r2, basis)
        mf = scf.UHF(mol).run()
        pt = mp.MP2(mf).run()
        return mf.e_tot + pt.e_corr
    if level.startswith("uhf/"):
        basis = level.split("/", 1)[1]
        mol = _molecule(r1, r2, basis)
        return scf.UHF(mol).run().e_tot
    raise ValueError(f"unknown level: {level}")


def scan(level: str, grid: tuple[float, ...] = GRID,
         cache_dir: str | Path = "runs/g3_h3", verbose: bool = True) -> dict:
    """Compute energies on the (r1, r2) grid, caching the result."""
    cache = Path(cache_dir) / f"{level.replace('/', '_')}.npz"
    grid = tuple(float(v) for v in grid)
    if cache.exists():
        data = np.load(cache)
        if tuple(np.round(data["grid"], 6)) == tuple(np.round(grid, 6)):
            return {"r1": data["r1"], "r2": data["r2"],
                    "energy": data["energy"], "level": level, "cached": True}
    r1s, r2s, energies = [], [], []
    for r1 in grid:
        for r2 in grid:
            r1s.append(r1)
            r2s.append(r2)
            energies.append(energy(r1, r2, level))
            if verbose:
                print(f"  {level:20s} r1={r1:.2f} r2={r2:.2f} "
                      f"E={energies[-1]:.8f} Ha", flush=True)
    r1 = np.array(r1s)
    r2 = np.array(r2s)
    e = np.array(energies)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, grid=np.array(grid), r1=r1, r2=r2, energy=e)
    return {"r1": r1, "r2": r2, "energy": e, "level": level, "cached": False}
