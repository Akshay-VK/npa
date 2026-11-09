"""Shared neighbour perception for the multi-particle variants.

Every variant sees the same features, so G2d isolates the contribution of
persistent state, not the contribution of perception (G2c showed perception
helps).
"""

from __future__ import annotations

import torch


def neighbour_features(x: torch.Tensor, cutoff: float = 1.0, sigma: float = 0.25):
    """Return (mean relative position, Gaussian density) for each particle.

    x: (B, N, D) -> agg: (B, N, D), rho: (B, N, 1)
    """
    d = x[:, :, None, :] - x[:, None, :, :]          # (B, N, N, D), x_i - x_j
    r2 = (d ** 2).sum(-1)                             # (B, N, N)
    r = (r2 + 1e-12).sqrt()
    eye = torch.eye(x.shape[1], device=x.device, dtype=torch.bool)[None]
    mask = (r < cutoff) & ~eye
    w = mask.to(x.dtype)
    rho = (torch.exp(-r2 / (2 * sigma ** 2)) * w).sum(-1, keepdim=True)
    agg = (d * w[..., None]).sum(2) / w.sum(2, keepdim=True).clamp(min=1.0)
    return agg, rho
