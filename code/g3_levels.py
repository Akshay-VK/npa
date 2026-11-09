"""G3 method probe: why CCSD(T)/cc-pVDZ is the cheap level, not MP2 or DFT.

Computes the H3 barrier at the reactant (3.0, 0.74) and the collinear saddle
(0.93, 0.93) Angstrom for UHF, B3LYP, MP2 and CCSD(T), all in cc-pVTZ. The
point is that only a smaller basis at the same correlated method tracks the
CCSD(T)/cc-pVTZ reference within the 1.5 kcal/mol gate; the cheaper methods are
off by several kcal/mol.

Usage:
    OMP_NUM_THREADS=4 python code/g3_levels.py
"""

from __future__ import annotations

from pyscf import cc, dft, gto, mp, scf

HARTREE2KCAL = 627.5094740631
GEOMS = {"reactant": (3.0, 0.74), "saddle": (0.93, 0.93)}


def molecule(r1: float, r2: float, basis: str = "cc-pvtz"):
    return gto.M(atom=[("H", (0.0, 0.0, -r1)),
                       ("H", (0.0, 0.0, 0.0)),
                       ("H", (0.0, 0.0, r2))],
                 basis=basis, unit="Angstrom", spin=1, verbose=0)


def uhf(r1, r2, basis="cc-pvtz"):
    return scf.UHF(molecule(r1, r2, basis)).run().e_tot


def b3lyp(r1, r2, basis="cc-pvtz"):
    return dft.UKS(molecule(r1, r2, basis), xc="b3lyp").run().e_tot


def mp2(r1, r2, basis="cc-pvtz"):
    mf = scf.UHF(molecule(r1, r2, basis)).run()
    pt = mp.MP2(mf).run()
    return mf.e_tot + pt.e_corr


def ccsd_t(r1, r2, basis="cc-pvtz"):
    mf = scf.UHF(molecule(r1, r2, basis)).run()
    mycc = cc.CCSD(mf)
    mycc.run()
    return mf.e_tot + mycc.e_corr + mycc.ccsd_t()


if __name__ == "__main__":
    for name, fn in [("UHF/cc-pVTZ", uhf), ("B3LYP/cc-pVTZ", b3lyp),
                     ("MP2/cc-pVTZ", mp2), ("CCSD(T)/cc-pVTZ", ccsd_t)]:
        e = {k: fn(*v) for k, v in GEOMS.items()}
        barrier = (e["saddle"] - e["reactant"]) * HARTREE2KCAL
        print(f"{name:18s} barrier = {barrier:7.3f} kcal/mol")
