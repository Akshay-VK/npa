"""3D visualization of a Transition1x reaction (reactant, TS, product)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from npa.data.transition1x import iter_reactions

ROOT = Path(__file__).resolve().parents[1]

ELEMENT_COLORS = {1: "#9ca3af", 6: "#1f2937", 7: "#3b82f6", 8: "#ef4444"}
ELEMENT_SIZES = {1: 30, 6: 80, 7: 80, 8: 80}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default=str(Path.home() / "npa-work/data/Transition1x_small.h5"))
    ap.add_argument("--rxn-idx", type=int, default=0)
    ap.add_argument("--out", type=str, default=str(ROOT / "docs/07-delivery/figures/g4-reaction-3d.png"))
    args = ap.parse_args()

    rxns = list(iter_reactions(args.data, split="test"))
    r = rxns[args.rxn_idx]
    z = r["atomic_numbers"]

    fig = plt.figure(figsize=(15, 5))
    titles = ["Reactant", "Transition state", "Product"]
    endpoints = [r["reactant"], r["transition_state"], r["product"]]
    for i, (title, ep) in enumerate(zip(titles, endpoints)):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        pos = ep["positions"][0]
        for ai in range(len(z)):
            ax.scatter(pos[ai, 0], pos[ai, 1], pos[ai, 2],
                       c=ELEMENT_COLORS.get(z[ai], "#888"),
                       s=ELEMENT_SIZES.get(z[ai], 50), edgecolors="black", linewidth=0.5)
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
    fig.suptitle(f"{r['formula']}  {r['rxn']}  ({len(z)} atoms)", fontsize=12)
    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
