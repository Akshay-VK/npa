"""Schematic diagram of the ReactivePairEnergy model."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parents[1]

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis("off")

def box(x, y, w, h, text, color="#3b82f6", fontsize=10):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                   facecolor=color, edgecolor="black", linewidth=1.2,
                                   alpha=0.85)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fontsize,
            fontweight="bold", color="white", wrap=True)

def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5))

# Input
box(0.5, 6.5, 2, 1, "Input\nz (B,N) atomic numbers\nx (B,N,3) positions", "#6b7280", 9)

# Element embedding
box(3.5, 6.5, 2, 1, "Element embedding\nnn.Embedding(4, 16)\n(B,N) -> (B,N,16)", "#8b5cf6", 9)

# Pairwise distances
box(3.5, 4.5, 2, 1, "Pairwise distances\nr_ij = ||x_i - x_j||\n(B,N,N)", "#10b981", 9)

# Smooth cutoff
box(3.5, 2.5, 2, 1, "Smooth cutoff\nfc = 0.5(1+cos(pi*r/rc))\n(B,N,N)", "#10b981", 9)

# Pair features
box(6.5, 5.5, 2.5, 1, "Pair features\nconcat(emb_i, emb_j, r/rc)\n(B,N,N,33)", "#f59e0b", 9)

# Pair MLP
box(6.5, 3.5, 2.5, 1, "Pair MLP\n33 -> hidden -> hidden -> 1\n(B,N,N,1)", "#f59e0b", 9)

# Multiply by cutoff
box(6.5, 1.5, 2.5, 1, "pair_e = pair_e * fc\n(B,N,N)", "#f59e0b", 9)

# Sum pairs
box(10, 4.5, 2, 1, "Sum over pairs / 2\ne_pair = sum(pair_e)/2\n(B,)", "#dc2626", 9)

# Per-element offset
box(10, 2.5, 2, 1, "Per-element offset\nsum(offset[z_i])\n(B,)", "#dc2626", 9)

# Total energy
box(10, 0.5, 2, 1, "Total energy\nE = e_pair + e_off\n(B,)", "#1f2937", 9)

# Forces
box(12.5, 0.5, 1.2, 1, "Forces\nF = -dE/dx\nvia autograd", "#7c3aed", 9)

# Arrows
arrow(2.5, 7, 3.5, 7)  # input -> embedding
arrow(2.5, 7, 3.5, 5)  # input -> distances (x)
arrow(4.5, 6.5, 4.5, 5.5)  # embedding -> pair features (via distances)
arrow(4.5, 4.5, 4.5, 3.5)  # distances -> cutoff
arrow(4.5, 2.5, 6.5, 2.0)  # cutoff -> multiply
arrow(5.5, 6.0, 6.5, 6.0)  # embedding -> pair features
arrow(7.75, 5.5, 7.75, 4.5)  # pair features -> MLP
arrow(7.75, 3.5, 7.75, 2.5)  # MLP -> multiply
arrow(9.0, 2.0, 10.0, 5.0)  # multiply -> sum pairs
arrow(11.0, 2.5, 11.0, 1.5)  # offset -> total (via sum)
arrow(12.0, 5.0, 12.0, 1.5)  # sum pairs -> total
arrow(12.0, 1.5, 12.5, 1.0)  # total -> forces

ax.set_title("ReactivePairEnergy: element-conditioned pairwise distance model", fontsize=14, fontweight="bold", pad=20)
fig.tight_layout()
out = ROOT / "docs/07-delivery/figures/model-schematic.png"
fig.savefig(out, dpi=150, facecolor="white")
print(f"wrote {out}")
