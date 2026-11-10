"""Element-conditioned pairwise-distance energy model for G4.

A small, rotation/translation-invariant energy model: a smooth-cutoff
pairwise MLP conditioned on element identity, plus a per-element offset.
Forces come from autograd. Handles variable atom counts via a mask.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn

ELEMENTS = {1: 0, 6: 1, 7: 2, 8: 3}
N_ELEM = 4
RCUT = 5.0


def _mlp(in_dim, hidden, out_dim):
    return nn.Sequential(
        nn.Linear(in_dim, hidden), nn.SiLU(),
        nn.Linear(hidden, hidden), nn.SiLU(),
        nn.Linear(hidden, out_dim),
    )


class ReactivePairEnergy(nn.Module):
    def __init__(self, hidden: int = 64, elem_dim: int = 16):
        super().__init__()
        self.elem_emb = nn.Embedding(N_ELEM, elem_dim)
        self.pair_net = _mlp(2 * elem_dim + 1, hidden, 1)
        self.offset = nn.Parameter(torch.zeros(N_ELEM))
        self.rcut = RCUT

    def _elem_idx(self, z):
        # z: (B, N) atomic numbers
        idx = torch.zeros_like(z)
        for el, i in ELEMENTS.items():
            idx = torch.where(z == el, torch.full_like(z, i), idx)
        return idx

    def energy(self, z, x, mask=None):
        # z: (B, N), x: (B, N, 3)
        B, N = z.shape
        ei = self._elem_idx(z)  # (B, N)
        emb = self.elem_emb(ei)  # (B, N, D)
        # pairwise distances
        diff = x[:, :, None, :] - x[:, None, :, :]  # (B, N, N, 3)
        r = diff.norm(dim=-1).clamp(min=1e-6)  # (B, N, N)
        # smooth cutoff
        rc = self.rcut
        fc = torch.where(r < rc, 0.5 * (1 + torch.cos(math.pi * r / rc)), torch.zeros_like(r))
        fc = fc * (r > 0).float()
        # zero diagonal
        eye = torch.eye(N, device=z.device, dtype=torch.bool)[None]
        fc = fc * (~eye).float()
        mask_pair = None
        if mask is not None:
            mp = mask[:, :, None] & mask[:, None, :]  # (B, N, N)
            fc = fc * mp.float()
        # pair features
        emb_i = emb[:, :, None, :].expand(B, N, N, -1)
        emb_j = emb[:, None, :, :].expand(B, N, N, -1)
        pair_feat = torch.cat([emb_i, emb_j, (r / rc).unsqueeze(-1)], dim=-1)  # (B,N,N,F)
        pair_e = self.pair_net(pair_feat).squeeze(-1)  # (B, N, N)
        pair_e = pair_e * fc
        # sum over pairs, divide by 2
        e_pair = pair_e.sum(dim=(1, 2)) * 0.5
        # per-element offset
        off = self.offset[ei]  # (B, N)
        if mask is not None:
            off = off * mask.float()
        e_off = off.sum(dim=1)
        return e_pair + e_off

    def forward(self, z, x, mask=None):
        return self.energy(z, x, mask)

    def force(self, z, x, mask=None):
        with torch.enable_grad():
            if not x.requires_grad:
                x = x.detach().requires_grad_(True)
            e = self.energy(z, x, mask).sum()
            g = torch.autograd.grad(e, x, create_graph=True)[0]
        return -g
