"""Animated GIF of the G2e hidden-phase world."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from npa.data.hidden_force import make_world

ROOT = Path(__file__).resolve().parents[1]


def main():
    world = make_world(n=12, k_spring=0.0, seed=0)
    xs, vs, qs = world.trajectory(60, 0.01)
    xs = xs.numpy()  # (T, N, 2)
    qs = qs.numpy()  # (T, N)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect("equal")
    ax.set_title("G2e world: 12 particles with hidden phases")

    sc = ax.scatter([], [], c=[], cmap="hsv", s=120, edgecolors="black",
                    linewidth=0.8, vmin=0, vmax=2 * np.pi)

    def update(frame):
        x = xs[frame]
        q = qs[frame]
        sc.set_offsets(x)
        sc.set_array(q)
        return (sc,)

    anim = FuncAnimation(fig, update, frames=len(xs), interval=100, blit=False)
    writer = PillowWriter(fps=10)
    out = ROOT / "docs/07-delivery/figures/g2e-world-anim.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out, writer=writer)
    print(f"wrote {out} ({len(xs)} frames)")


if __name__ == "__main__":
    main()
