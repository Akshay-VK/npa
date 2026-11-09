"""G3 figure: the H3 reference surface and the barrier-error gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from npa.data.h3 import HARTREE2KCAL

ROOT = Path(__file__).resolve().parents[1]
ref = np.load(ROOT / "runs/g3_h3/ccsd(t)_cc-pvtz.npz")
final = json.loads((ROOT / "runs/g3_h3/final.json").read_text())

r1 = ref["r1"]
r2 = ref["r2"]
e = ref["energy"]
grid = ref["grid"]
n = len(grid)
e_rel = (e - e[np.where((np.isclose(r1, 3.0)) & (np.isclose(r2, 0.74)))[0][0]]) * HARTREE2KCAL
R1 = r1.reshape(n, n)
R2 = r2.reshape(n, n)
E = e_rel.reshape(n, n)

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), layout="constrained",
                         gridspec_kw={"width_ratios": [1.15, 1.0]})

# --- Panel A: reference PES -------------------------------------------------
ax = axes[0]
mesh = ax.pcolormesh(R1, R2, np.clip(E, 0, 30), shading="auto", cmap="viridis",
                     vmin=0, vmax=30)
cbar = fig.colorbar(mesh, ax=ax, pad=0.02)
cbar.set_label("Relative energy (kcal/mol, capped at 30)")
ax.plot([3.0, 0.93, 0.74], [0.74, 0.93, 3.0], "w--", linewidth=1.4,
        label="reaction path")
for (x, y, label, dx, dy) in [
    (3.0, 0.74, "reactant\nH + H$_2$", -0.7, 0.45),
    (0.93, 0.93, "saddle\n0.93 Å", 0.35, -0.55),
    (0.74, 3.0, "product\nH$_2$ + H", 0.35, -0.55),
]:
    ax.plot(x, y, "o", color="white", markeredgecolor="black", markersize=7, zorder=5)
    ax.annotate(label, (x, y), xytext=(x + dx, y + dy), color="white",
                fontsize=8.5, fontweight="bold", zorder=6,
                arrowprops=dict(arrowstyle="-", color="white", lw=0.8))
ax.set_xlabel("$r_1$ = H$_A$–H$_B$ (Å)")
ax.set_ylabel("$r_2$ = H$_B$–H$_C$ (Å)")
ax.set_title("CCSD(T)/cc-pVTZ reference surface")
ax.set_xlim(grid[0], grid[-1])
ax.set_ylim(grid[0], grid[-1])
ax.legend(loc="upper right", fontsize=8, framealpha=0.85)

# --- Panel B: barrier-error gate -------------------------------------------
ax = axes[1]
conds = ["cheap_to_ref", "mp2_to_ref", "ref_holdout"]
labels = ["cheap → ref\nCCSD(T)/VDZ", "MP2 → ref\nnegative control",
          "ref holdout\nsaddle unseen"]
models = [("mlp", "MLP (main)", "#3b82f6"), ("pairwise", "pairwise Morse", "#f59e0b")]
width = 0.36
xs = np.arange(len(conds))
for k, (kind, name, colour) in enumerate(models):
    means = [final["runs"][kind][c]["summary"]["barrier_err"]["mean"] for c in conds]
    stds = [final["runs"][kind][c]["summary"]["barrier_err"]["std"] for c in conds]
    pos = xs + (k - 0.5) * width
    ax.bar(pos, means, width, yerr=stds, capsize=3, color=colour, alpha=0.75,
           edgecolor="black", linewidth=0.6, label=name, zorder=2)
    for x, m in zip(pos, means):
        ax.text(x, m + 0.08, f"{m:.2f}", ha="center", va="bottom", fontsize=8,
                fontweight="bold")
ax.axhline(1.5, color="#dc2626", linestyle="--", linewidth=1.1, zorder=3)
ax.text(len(conds) - 0.55, 1.58, "gate 1.5", color="#dc2626", fontsize=8.5,
        ha="right", va="bottom", fontweight="bold")
ax.set_xticks(xs)
ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylabel("|barrier error| (kcal/mol)")
ax.set_title("Barrier error vs the CCSD(T)/cc-pVTZ reference")
ax.set_ylim(0, 3.7)
ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

fig.suptitle("G3: H + H$_2$ → H$_2$ + H barrier from cheap labels (3 seeds)",
             fontsize=12, fontweight="bold")
fig.text(0.5, -0.02,
         "Left: the reference path. Right: mean ± std over three seeds; lower is "
         "better. The MLP (blue) trained on cc-pVDZ labels passes the 1.5 kcal/mol "
         "gate; its MP2 control fails it. The pairwise model (amber) is secondary: "
         "it passes cheap-to-ref but does not separate the MP2 control.",
         ha="center", fontsize=7.5, color="#4b5563")

out = ROOT / "docs/07-delivery/figures/g3-h3-results.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
print(f"wrote {out}")
