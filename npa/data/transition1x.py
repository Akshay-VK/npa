"""Transition1x data loader, filtering, metrics, and mock generator.

Memory-efficient: builds a lightweight index of (formula, rxn, frame) tuples
without loading the data into RAM. Frames are read from the HDF5 file on
demand in __getitem__. This keeps memory O(index size) instead of O(dataset).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

import h5py
import numpy as np
import torch

EV_TO_KCAL = 23.0605

REFERENCE_ENERGIES = {
    1: -13.62222753701504,
    6: -1029.4130839658328,
    7: -1484.8710358098756,
    8: -2041.8396277138045,
}

ALLOWED_ELEMENTS = {1, 6, 7, 8}


def get_molecular_reference_energy(atomic_numbers):
    return sum(REFERENCE_ENERGIES[z] for z in atomic_numbers)


def heavy_atom_count(atomic_numbers):
    return sum(1 for z in atomic_numbers if z > 1)


def barrier_kcal(reaction):
    ts = reaction["transition_state"]
    reactant = reaction["reactant"]
    return float((ts["wB97x_6-31G(d).energy"] - reactant["wB97x_6-31G(d).energy"]).ravel()[0]) * EV_TO_KCAL


def reaction_energy_kcal(reaction):
    product = reaction["product"]
    reactant = reaction["reactant"]
    return float((product["wB97x_6-31G(d).energy"] - reactant["wB97x_6-31G(d).energy"]).ravel()[0]) * EV_TO_KCAL


def _read_group(grp):
    return {
        "atomic_numbers": [int(z) for z in grp["atomic_numbers"][...]],
        "positions": np.asarray(grp["positions"][...], dtype=np.float64),
        "wB97x_6-31G(d).energy": np.asarray(grp["wB97x_6-31G(d).energy"][...], dtype=np.float64),
        "wB97x_6-31G(d).forces": np.asarray(grp["wB97x_6-31G(d).forces"][...], dtype=np.float64),
    }


def iter_reactions(path, split="data", max_heavy=7, elements=ALLOWED_ELEMENTS):
    """Yield reaction dicts. Use only for small datasets or tests."""
    with h5py.File(path, "r") as f:
        root = f[split]
        for formula, fgrp in root.items():
            for rxn, rgrp in fgrp.items():
                atomic_numbers = [int(z) for z in rgrp["atomic_numbers"][...]]
                if any(z not in elements for z in atomic_numbers):
                    continue
                if heavy_atom_count(atomic_numbers) > max_heavy:
                    continue
                reactant = _read_group(rgrp["reactant"])
                product = _read_group(rgrp["product"])
                ts = _read_group(rgrp["transition_state"])
                path_data = _read_group(rgrp)
                yield {
                    "formula": formula,
                    "rxn": rxn,
                    "split": split,
                    "atomic_numbers": atomic_numbers,
                    "positions": path_data["positions"],
                    "energy": path_data["wB97x_6-31G(d).energy"],
                    "forces": path_data["wB97x_6-31G(d).forces"],
                    "reactant": reactant,
                    "product": product,
                    "transition_state": ts,
                }


def verify_md5(path, expected="faab0413cf6b042b6d50e6272dea9a8c", chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest() == expected, h.hexdigest()


def make_mock_hdf5(path, n_formulas=3, n_rxns_per_formula=2, n_frames=5,
                   n_atoms_range=(3, 5), seed=0):
    rng = np.random.default_rng(seed)
    with h5py.File(path, "w") as f:
        data = f.create_group("data")
        formulas = []
        for fi in range(n_formulas):
            formula = f"C{2+fi}H{4+fi}N{1 if fi % 2 == 0 else 0}O{1 if fi % 3 == 0 else 0}".rstrip("0")
            if formula not in data:
                fgrp = data.create_group(formula)
            else:
                fgrp = data[formula]
            for ri in range(n_rxns_per_formula):
                rxn = f"rxn{fi * 100 + ri:04d}"
                rgrp = fgrp.create_group(rxn)
                n_atoms = int(rng.integers(n_atoms_range[0], n_atoms_range[1] + 1))
                z = np.array([6] + [1] * (n_atoms - 1), dtype=np.int64)
                positions = np.zeros((n_frames, n_atoms, 3), dtype=np.float64)
                for fr in range(n_frames):
                    positions[fr] = rng.normal(scale=0.3, size=(n_atoms, 3))
                    positions[fr, 0, 0] += 0.5 * fr / max(n_frames - 1, 1)
                energy = np.array([float(np.sum(p ** 2) * 0.5 + 0.1 * fr)
                                   for fr, p in enumerate(positions)], dtype=np.float64)
                forces = np.array([-p for p in positions], dtype=np.float64) * 0.5

                def _endpoint(name, i):
                    ii = i if i >= 0 else len(energy) + i
                    eg = rgrp.create_group(name)
                    eg.create_dataset("atomic_numbers", data=z)
                    eg.create_dataset("positions", data=positions[ii:ii + 1])
                    eg.create_dataset("wB97x_6-31G(d).energy", data=energy[ii:ii + 1])
                    eg.create_dataset("wB97x_6-31G(d).forces", data=forces[ii:ii + 1])
                    eg.create_dataset("hash", data=int(hashlib.sha1(positions[ii].tobytes()).hexdigest(), 16) % (10 ** 8))
                    return eg
                _endpoint("reactant", 0)
                _endpoint("product", -1)
                ts_idx = int(np.argmax(energy))
                _endpoint("transition_state", ts_idx)
                rgrp.create_dataset("atomic_numbers", data=z)
                rgrp.create_dataset("positions", data=positions)
                rgrp.create_dataset("wB97x_6-31G(d).energy", data=energy)
                rgrp.create_dataset("wB97x_6-31G(d).forces", data=forces)
                formulas.append(formula)

        train = f.create_group("train")
        val = f.create_group("val")
        test = f.create_group("test")
        uniq = sorted(set(formulas))
        for i, fm in enumerate(uniq):
            if i < len(uniq) - 2:
                train[fm] = h5py.SoftLink(f"/data/{fm}")
            elif i == len(uniq) - 2:
                val[fm] = h5py.SoftLink(f"/data/{fm}")
            else:
                test[fm] = h5py.SoftLink(f"/data/{fm}")
    return path


@dataclass
class _IndexEntry:
    formula: str
    rxn: str
    frame_idx: int


class Transition1xIndex:
    """Lightweight index over an HDF5 file. Stores only (formula, rxn, frame)
    tuples; no data is loaded into RAM."""

    def __init__(self, path, split="train", max_heavy=7, elements=ALLOWED_ELEMENTS,
                 max_frames=None, seed=0):
        self.path = path
        self.split = split
        self.max_heavy = max_heavy
        self.elements = elements
        self.max_frames = max_frames
        rng = np.random.default_rng(seed)

        self.entries: list[_IndexEntry] = []
        with h5py.File(path, "r") as f:
            root = f[split]
            for formula in root.keys():
                fgrp = root[formula]
                # resolve soft link to data group
                data_grp = f["data"][formula]
                for rxn in data_grp.keys():
                    rgrp = data_grp[rxn]
                    z = [int(x) for x in rgrp["atomic_numbers"][...]]
                    if any(zz not in elements for zz in z):
                        continue
                    if heavy_atom_count(z) > max_heavy:
                        continue
                    n_frames = rgrp["wB97x_6-31G(d).energy"].shape[0]
                    idxs = list(range(n_frames))
                    if max_frames is not None and n_frames > max_frames:
                        idxs = sorted(rng.choice(idxs, size=max_frames, replace=False).tolist())
                    for fi in idxs:
                        self.entries.append(_IndexEntry(formula, rxn, fi))

    def __len__(self):
        return len(self.entries)


class Transition1xDataset(torch.utils.data.Dataset):
    """Memory-efficient dataset. Reads frames from HDF5 on demand."""

    def __init__(self, path, split="train", max_heavy=7, elements=ALLOWED_ELEMENTS,
                 max_frames=None, seed=0):
        self.path = path
        self.index = Transition1xIndex(path, split=split, max_heavy=max_heavy,
                                      elements=elements, max_frames=max_frames,
                                      seed=seed)
        # cache for the HDF5 handle (one per process)
        self._h5 = None

    def _get_h5(self):
        if self._h5 is None:
            self._h5 = h5py.File(self.path, "r")
        return self._h5

    def __len__(self):
        return len(self.index)

    def __getitem__(self, i):
        entry = self.index.entries[i]
        f = self._get_h5()
        rgrp = f["data"][entry.formula][entry.rxn]
        z = [int(x) for x in rgrp["atomic_numbers"][...]]
        positions = rgrp["positions"][entry.frame_idx]
        energy = float(rgrp["wB97x_6-31G(d).energy"][entry.frame_idx])
        forces = np.asarray(rgrp["wB97x_6-31G(d).forces"][entry.frame_idx], dtype=np.float64)
        # reactant/ts/product endpoints
        reactant = {
            "atomic_numbers": z,
            "positions": np.asarray(rgrp["reactant"]["positions"][...], dtype=np.float64),
            "wB97x_6-31G(d).energy": np.asarray(rgrp["reactant"]["wB97x_6-31G(d).energy"][...], dtype=np.float64),
            "wB97x_6-31G(d).forces": np.asarray(rgrp["reactant"]["wB97x_6-31G(d).forces"][...], dtype=np.float64),
        }
        product = {
            "atomic_numbers": z,
            "positions": np.asarray(rgrp["product"]["positions"][...], dtype=np.float64),
            "wB97x_6-31G(d).energy": np.asarray(rgrp["product"]["wB97x_6-31G(d).energy"][...], dtype=np.float64),
            "wB97x_6-31G(d).forces": np.asarray(rgrp["product"]["wB97x_6-31G(d).forces"][...], dtype=np.float64),
        }
        ts = {
            "atomic_numbers": z,
            "positions": np.asarray(rgrp["transition_state"]["positions"][...], dtype=np.float64),
            "wB97x_6-31G(d).energy": np.asarray(rgrp["transition_state"]["wB97x_6-31G(d).energy"][...], dtype=np.float64),
            "wB97x_6-31G(d).forces": np.asarray(rgrp["transition_state"]["wB97x_6-31G(d).forces"][...], dtype=np.float64),
        }
        ref = get_molecular_reference_energy(z)
        ae = energy - ref
        return {"z": torch.tensor(z, dtype=torch.long),
                "x": torch.tensor(positions, dtype=torch.float32),
                "energy": torch.tensor(energy, dtype=torch.float32),
                "atomization_energy": torch.tensor(ae, dtype=torch.float32),
                "forces": torch.tensor(forces, dtype=torch.float32),
                "formula": entry.formula,
                "rxn": entry.rxn,
                "reactant": reactant,
                "product": product,
                "transition_state": ts}

    def __del__(self):
        if self._h5 is not None:
            try:
                self._h5.close()
            except Exception:
                pass


def collate(batch):
    max_n = max(b["z"].shape[0] for b in batch)
    B = len(batch)
    z = torch.zeros(B, max_n, dtype=torch.long)
    x = torch.zeros(B, max_n, 3, dtype=torch.float32)
    mask = torch.zeros(B, max_n, dtype=torch.bool)
    e = torch.zeros(B, dtype=torch.float32)
    ae = torch.zeros(B, dtype=torch.float32)
    frc = torch.zeros(B, max_n, 3, dtype=torch.float32)
    for i, b in enumerate(batch):
        n = b["z"].shape[0]
        z[i, :n] = b["z"]
        x[i, :n] = b["x"]
        mask[i, :n] = True
        e[i] = b["energy"]
        ae[i] = b["atomization_energy"]
        frc[i, :n] = b["forces"]
    return {"z": z, "x": x, "mask": mask, "energy": e,
            "atomization_energy": ae, "forces": frc}
