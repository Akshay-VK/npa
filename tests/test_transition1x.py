"""Tests for the Transition1x data loader and mock generator."""
import os
import tempfile
import unittest

import h5py
import numpy as np

from npa.data.transition1x import (
    iter_reactions, make_mock_hdf5, verify_md5, heavy_atom_count,
    barrier_kcal, reaction_energy_kcal, ALLOWED_ELEMENTS,
    Transition1xDataset, collate,
)


class TestMockSchema(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".h5")
        os.close(self.fd)
        make_mock_hdf5(self.path, n_formulas=3, n_rxns_per_formula=2, n_frames=5)

    def tearDown(self):
        os.remove(self.path)

    def test_top_level_groups(self):
        with h5py.File(self.path, "r") as f:
            self.assertEqual(sorted(f.keys()), ["data", "test", "train", "val"])

    def test_schema(self):
        with h5py.File(self.path, "r") as f:
            formula = list(f["data"].keys())[0]
            rxn = list(f["data"][formula].keys())[0]
            grp = f["data"][formula][rxn]
            for ds in ["atomic_numbers", "positions", "wB97x_6-31G(d).energy",
                       "wB97x_6-31G(d).forces"]:
                self.assertIn(ds, grp)
            for sub in ["reactant", "product", "transition_state"]:
                self.assertIn(sub, grp)
                for ds in ["atomic_numbers", "positions", "wB97x_6-31G(d).energy",
                           "wB97x_6-31G(d).forces", "hash"]:
                    self.assertIn(ds, grp[sub])

    def test_iter_reactions(self):
        rxns = list(iter_reactions(self.path, split="train"))
        self.assertGreater(len(rxns), 0)
        for r in rxns:
            self.assertIn("formula", r)
            self.assertIn("atomic_numbers", r)
            self.assertIn("positions", r)
            self.assertIn("energy", r)
            self.assertIn("forces", r)
            self.assertIn("reactant", r)
            self.assertIn("product", r)
            self.assertIn("transition_state", r)

    def test_filter(self):
        rxns = list(iter_reactions(self.path, split="train", max_heavy=0))
        # all mock reactions have heavy atoms (C), so none should pass
        self.assertEqual(len(rxns), 0)

    def test_barrier_and_reaction_energy(self):
        rxns = list(iter_reactions(self.path, split="data"))
        r = rxns[0]
        b = barrier_kcal(r)
        re = reaction_energy_kcal(r)
        self.assertTrue(np.isfinite(b))
        self.assertTrue(np.isfinite(re))

    def test_dataset_and_collate(self):
        ds = Transition1xDataset(self.path, split="train", max_frames=3)
        self.assertGreater(len(ds), 0)
        from torch.utils.data import DataLoader
        dl = DataLoader(ds, batch_size=2, collate_fn=collate)
        batch = next(iter(dl))
        self.assertIn("z", batch)
        self.assertIn("mask", batch)
        self.assertEqual(batch["z"].shape[0], 2)
        self.assertEqual(batch["x"].shape[2], 3)

    def test_verify_md5(self):
        import hashlib
        h = hashlib.md5()
        with open(self.path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        digest = h.hexdigest()
        ok, got = verify_md5(self.path, expected=digest)
        self.assertTrue(ok)
        self.assertEqual(got, digest)


if __name__ == "__main__":
    unittest.main()
