"""Tests for the G2e arms."""
import unittest

import torch

from npa.models.mp_g2e import build_variant


class TestG2eArms(unittest.TestCase):
    def setUp(self):
        self.cfg = {"hidden": 16, "state_dim": 4, "history": 4}

    def _check_force(self, kind, x, s):
        model = build_variant(kind, dim=2, hidden=self.cfg["hidden"],
                              state_dim=self.cfg["state_dim"])
        model.eval()
        F, _ = model.force_and_ds(x, s)
        self.assertEqual(F.shape, x.shape)

    def test_v2h_shape(self):
        x = torch.randn(1, 4, 2)
        s = torch.zeros(1, 4, 4, 2)
        self._check_force("v2h", x, s)

    def test_v3b_ema_shape(self):
        x = torch.randn(1, 4, 2)
        s = torch.zeros(1, 4, 4)
        self._check_force("v3b_ema", x, s)

    def test_v3b_residual_shape(self):
        x = torch.randn(1, 4, 2)
        s = torch.zeros(1, 4, 4)
        self._check_force("v3b_residual", x, s)

    def test_v3b_combined_shape(self):
        x = torch.randn(1, 4, 2)
        s = torch.zeros(1, 4, 4)
        self._check_force("v3b_combined", x, s)

    def test_v2h_force_finite_difference(self):
        model = build_variant("v2h", dim=2, hidden=16)
        model.eval()
        x = torch.randn(1, 4, 2, requires_grad=True)
        s = torch.zeros(1, 4, 4, 2)
        F, _ = model.force_and_ds(x.detach().requires_grad_(True), s)
        # finite difference
        eps = 1e-4
        Ffd = torch.zeros_like(x)
        for i in range(x.shape[1]):
            for j in range(x.shape[2]):
                xp = x.clone(); xp[0, i, j] += eps
                xm = x.clone(); xm[0, i, j] -= eps
                with torch.no_grad():
                    ep = model.energy(xp.detach(), s).sum().item()
                    em = model.energy(xm.detach(), s).sum().item()
                Ffd[0, i, j] = -(ep - em) / (2 * eps)
        self.assertTrue(torch.allclose(F, Ffd, atol=1e-2))

    def test_ema_update_bounded(self):
        model = build_variant("v3b_ema", dim=2, hidden=16, state_dim=4)
        model.eval()
        x = torch.randn(1, 4, 2)
        s = torch.zeros(1, 4, 4)
        F, ds = model.force_and_ds(x, s)
        s2 = s + ds
        # EMA should keep state bounded
        self.assertTrue(torch.isfinite(s2).all())

    def test_smoke_train(self):
        import torch.nn as nn
        model = build_variant("v3b_combined", dim=2, hidden=16, state_dim=4)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        for _ in range(2):
            x = torch.randn(1, 4, 2)
            s = torch.zeros(1, 4, 4)
            opt.zero_grad()
            e = model.energy(x, s).sum()
            e.backward()
            opt.step()
        self.assertTrue(torch.isfinite(model.energy(torch.randn(1, 4, 2),
                                                   torch.zeros(1, 4, 4))).all())


if __name__ == "__main__":
    unittest.main()


class TestG2eCLI(unittest.TestCase):
    def test_state_dim_flag_default(self):
        from code.g2e_train import build_parser
        args = build_parser().parse_args([])
        self.assertEqual(args.state_dim, 4)

    def test_state_dim_flag_override(self):
        from code.g2e_train import build_parser
        args = build_parser().parse_args(["--state-dim", "16"])
        self.assertEqual(args.state_dim, 16)
