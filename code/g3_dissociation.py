"""G3 dissociation check at the roadmap's 20 Angstrom separation.

The training grid stops at 6 Angstrom. This script trains the two molecular
models on the cheap labels exactly as in ``code/g3_h3.py`` (seed 0) and probes
the energy as one H atom is pulled away at 6, 10, 20 and 40 Angstrom, with the
H2 fragment held at its equilibrium bond (0.74 Angstrom). The reference value at
20 Angstrom is computed directly at CCSD(T)/cc-pVTZ; at 40 Angstrom the
reference is the isolated-fragment limit, so the 20 Angstrom value is the honest
target.

A correct dissociation limit means the probe is flat: the energy at 20 Angstrom
should match the energy at 3 Angstrom to within a small tolerance. The report
uses this to decide whether the 6 Angstrom pass generalises to the roadmap's
20 Angstrom requirement.

Usage:
    OMP_NUM_THREADS=4 python code/g3_dissociation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import torch

from g3_h3 import LEVELS, LOW_ENERGY, to_xy, train_model
from npa.data.h3 import HARTREE2KCAL, REACTANT, energy, h3_positions, scan

PROBES = (3.0, 6.0, 10.0, 20.0, 40.0)


def main() -> None:
    cheap = to_xy(scan(LEVELS["cheap"], verbose=False))
    x_cheap, y_cheap, _ = cheap
    mask = y_cheap < LOW_ENERGY

    models = {}
    for kind in ("mlp", "pairwise"):
        models[kind] = train_model(x_cheap[mask], y_cheap[mask], kind,
                                   steps=3000, seed=0, lr=5e-3)

    # Reference energies: 3 and 6 A are in the cached grid; 10, 20 and 40 A are
    # computed here so the 20 A target is not an interpolation.
    raw_ref = scan(LEVELS["ref"], verbose=False)
    e0_ref = raw_ref["energy"][
        int(np.where(np.isclose(raw_ref["r1"], REACTANT[0]) &
                     np.isclose(raw_ref["r2"], REACTANT[1]))[0][0])]
    ref_rel = {}
    for r1 in PROBES:
        if r1 <= 6.0:
            i = int(np.where(np.isclose(raw_ref["r1"], r1) &
                             np.isclose(raw_ref["r2"], REACTANT[1]))[0][0])
            ref_rel[r1] = float((raw_ref["energy"][i] - e0_ref) * HARTREE2KCAL)
        else:
            e = energy(r1, REACTANT[1], LEVELS["ref"])
            ref_rel[r1] = float((e - e0_ref) * HARTREE2KCAL)

    print(f"{'r1 (A)':>8s} {'reference':>10s} {'MLP':>10s} {'pairwise':>10s}")
    print("-" * 42)
    for r1 in PROBES:
        x = torch.tensor(h3_positions(r1, REACTANT[1]), dtype=torch.float32)[None]
        row = [ref_rel[r1]]
        for kind in ("mlp", "pairwise"):
            m = models[kind]
            m.eval()
            with torch.no_grad():
                e = m(x).item()
                e0 = m(torch.tensor(h3_positions(*REACTANT),
                                    dtype=torch.float32)[None]).item()
            row.append(e - e0)
        print(f"{r1:8.1f} {row[0]:10.3f} {row[1]:10.3f} {row[2]:10.3f}")
    print("\nAll energies are kcal/mol relative to the reactant at 3.0 A.")
    print("A correct limit is flat: the 20 A value should be near zero.")


if __name__ == "__main__":
    main()
