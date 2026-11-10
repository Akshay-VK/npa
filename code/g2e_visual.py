"""Visualize the G2e hidden-phase world: particles colored by hidden phase."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from npa.data.hidden_force import make_world

ROOT = Path(__file__).resolve().parents[1]


def main():
    world = make_world(n=12, k_spring=0.0, seed=0)
    xs, vs, qs = world.trajectory(1, 0.01)
    x = xs[0].numpy()
    q = qs[0].numpy()

    fig, ax = plt.subplots(figsize=(7, 7))
    # particles colored by phase
    sc = ax.scatter(x[:, 0], x[:, 1], c=q, cmap="hsv", s=120, edgecolors="black",
                    linewidth=0.8, vmin=0, vmax=2 * np.pi)
    # hidden force arrows
    Fh = world.amp * np.stack([np.cos(q), np.sin(q)], axis=-1)
    ax.quiver(x[:, 0], x[:, 1], Fh[:, 0], Fh[:, 1], color="black", alpha=0.6,
              scale=8, width=0.005)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect("equal")
    ax.set_title("G2e world: 12 particles, colored by hidden phase")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    cbar = fig.colorbar(sc, ax=ax, label="hidden phase q (rad)")
    fig.tight_layout()
    out = ROOT / "docs/07-delivery/figures/g2e-world.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
