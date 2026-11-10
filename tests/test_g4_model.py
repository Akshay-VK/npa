"""Tests for the G4 reactive model."""
import math
import unittest

import torch

from npa.models.reactive import ReactivePairEnergy


class TestReactiveModel(unittest.TestCase):
    def setUp(self):
        self.model = ReactivePairEnergy(hidden=16)
        self.z = torch.tensor([[6, 1, 1, 8]], dtype=torch.long)
        self.x = torch.tensor([[[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0],
                                [0.0, 0.0, 1.0]]], dtype=torch.float32)

    def test_forward_shape(self):
        e = self.model.energy(self.z, self.x)
        self.assertEqual(e.shape, (1,))

    def test_variable_n(self):
        z2 = torch.tensor([[6, 1]], dtype=torch.long)
        x2 = torch.tensor([[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]], dtype=torch.float32)
        e = self.model.energy(z2, x2)
        self.assertEqual(e.shape, (1,))

    def test_mask(self):
        mask = torch.tensor([[True, True, False, False]])
        e = self.model.energy(self.z, self.x, mask=mask)
        self.assertTrue(torch.isfinite(e).all())

    def test_translation_invariance(self):
        t = torch.tensor([[[2.0, -1.0, 0.5]]])
        e1 = self.model.energy(self.z, self.x)
        e2 = self.model.energy(self.z, self.x + t)
        self.assertTrue(torch.allclose(e1, e2, atol=1e-5))

    def test_rotation_invariance(self):
        # 90 deg around z
        R = torch.tensor([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]], dtype=torch.float32)
        xr = self.x @ R.T
        e1 = self.model.energy(self.z, self.x)
        e2 = self.model.energy(self.z, xr)
        self.assertTrue(torch.allclose(e1, e2, atol=1e-5))

    def test_force_consistency(self):
        x = self.x.clone().requires_grad_(True)
        e = self.model.energy(self.z, x).sum()
        g = torch.autograd.grad(e, x)[0]
        F = self.model.force(self.z, self.x)
        self.assertTrue(torch.allclose(F, -g, atol=1e-4))

    def test_smoke_train(self):
        opt = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        for _ in range(3):
            opt.zero_grad()
            e = self.model.energy(self.z, self.x)
            loss = (e ** 2).mean()
            loss.backward()
            opt.step()
        self.assertTrue(torch.isfinite(self.model.energy(self.z, self.x)).all())


if __name__ == "__main__":
    unittest.main()
