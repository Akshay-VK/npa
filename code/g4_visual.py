"""Visualize a Transition1x reaction path."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from npa.data.transition1x import iter_reactions

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default=str(Path.home() / "npa-work/data/Transition1x_small.h5"))
    ap.add_argument("--rxn-idx", type=int, default=0)
    ap.add_argument("--out", type=str, default=str(ROOT / "docs/07-delivery/figures/g4-reaction-path.png"))
    args = ap.parse_args()

    rxns = list(iter_reactions(args.data, split="test"))
    r = rxns[args.rxn_idx]
    z = r["atomic_numbers"]
    positions = r["positions"]  # (M, A, 3)
    energy = r["energy"]  # (M,)
    forces = r["forces"]  # (M, A, 3)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Energy profile
    ax = axes[0]
    ax.plot(range(len(energy)), energy * 23.0605, "o-", color="#3b82f6", markersize=4)
    ts_idx = int(np.argmax(energy))
    ax.axvline(ts_idx, color="#dc2626", linestyle="--", label="TS")
    ax.set_xlabel("Frame along path")
    ax.set_ylabel("Energy (kcal/mol, relative)")
    ax.set_title(f"Reaction path: {r['formula']} / {r['rxn']}")
    ax.legend()

    # 2D projection of positions (first two dims)
    ax = axes[1]
    colors = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
    for ai in range(len(z)):
        xs = positions[:, ai, 0]
        ys = positions[:, ai, 1]
        ax.plot(xs, ys, "-o", color=colors[ai % len(colors)], markersize=3,
                label=f"atom {ai} (Z={z[ai]})")
        ax.scatter([xs[0]], [ys[0]], color=colors[ai % len(colors)], s=80, marker="s")
        ax.scatter([xs[-1]], [ys[-1]], color=colors[ai % len(colors)], s=80, marker="^")
    ax.set_xlabel("x (Å)")
    ax.set_ylabel("y (Å)")
    ax.set_title("Atomic trajectories (square=start, triangle=end)")
    ax.legend(fontsize=7, loc="best")

    # Force magnitude per frame
    ax = axes[2]
    fm = np.array([np.linalg.norm(forces[fr], axis=1).mean() for fr in range(len(forces))])
    ax.plot(range(len(fm)), fm, "o-", color="#f59e0b", markersize=4)
    ax.axvline(ts_idx, color="#dc2626", linestyle="--", label="TS")
    ax.set_xlabel("Frame along path")
    ax.set_ylabel("Mean force magnitude (eV/Å)")
    ax.set_title("Force magnitude along path")
    ax.legend()

    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, facecolor="white")
    print(f"wrote {args.out}")
    print(f"reaction: {r['formula']} {r['rxn']}, {len(z)} atoms, {len(energy)} frames, TS at frame {ts_idx}")


if __name__ == "__main__":
    main()
