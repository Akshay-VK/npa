"""Animated GIF of a Transition1x reaction path."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from npa.data.transition1x import iter_reactions

ROOT = Path(__file__).resolve().parents[1]

ELEMENT_COLORS = {1: "#9ca3af", 6: "#1f2937", 7: "#3b82f6", 8: "#ef4444"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default=str(Path.home() / "npa-work/data/Transition1x_small.h5"))
    ap.add_argument("--rxn-idx", type=int, default=0)
    ap.add_argument("--stride", type=int, default=5)
    ap.add_argument("--out", type=str, default=str(ROOT / "docs/07-delivery/figures/g4-reaction-anim.gif"))
    args = ap.parse_args()

    rxns = list(iter_reactions(args.data, split="test"))
    r = rxns[args.rxn_idx]
    z = r["atomic_numbers"]
    positions = r["positions"][::args.stride]  # (M, A, 3)
    energy = r["energy"][::args.stride]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: 2D projection of atoms
    ax1.set_xlim(positions[:, :, 0].min() - 1, positions[:, :, 0].max() + 1)
    ax1.set_ylim(positions[:, :, 1].min() - 1, positions[:, :, 1].max() + 1)
    ax1.set_aspect("equal")
    ax1.set_title("Atomic positions")
    ax1.set_xlabel("x (Å)")
    ax1.set_ylabel("y (Å)")

    scatters = []
    for ai in range(len(z)):
        sc = ax1.scatter([], [], c=ELEMENT_COLORS.get(z[ai], "#888"), s=80,
                         edgecolors="black", linewidth=0.5, label=f"Z={z[ai]}")
        scatters.append(sc)

    # Right: energy profile with moving marker
    ax2.plot(range(len(energy)), energy * 23.0605, "k-", alpha=0.3)
    marker, = ax2.plot([], [], "ro", markersize=8)
    ax2.set_xlim(0, len(energy) - 1)
    ax2.set_ylim(energy.min() * 23.0605 - 5, energy.max() * 23.0605 + 5)
    ax2.set_xlabel("Frame")
    ax2.set_ylabel("Energy (kcal/mol)")
    ax2.set_title("Energy along reaction path")

    def update(frame):
        for ai in range(len(z)):
            scatters[ai].set_offsets([[positions[frame, ai, 0], positions[frame, ai, 1]]])
        marker.set_data([frame], [energy[frame] * 23.0605])
        return scatters + [marker]

    anim = FuncAnimation(fig, update, frames=len(positions), interval=100, blit=True)
    writer = PillowWriter(fps=10)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    anim.save(args.out, writer=writer)
    print(f"wrote {args.out} ({len(positions)} frames)")

    # Also save a static mid-frame
    mid = len(positions) // 2
    fig2, ax = plt.subplots(figsize=(6, 6))
    for ai in range(len(z)):
        ax.scatter(positions[mid, ai, 0], positions[mid, ai, 1],
                   c=ELEMENT_COLORS.get(z[ai], "#888"), s=100, edgecolors="black")
    ax.set_title(f"Mid-path frame {mid}")
    ax.set_aspect("equal")
    fig2.savefig(str(Path(args.out).with_suffix(".png")), dpi=150)
    print(f"wrote {Path(args.out).with_suffix('.png')}")


if __name__ == "__main__":
    main()
