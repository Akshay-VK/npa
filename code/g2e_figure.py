"""G2e figure: force MAE, rollout drift, and state-probe R2 by arm."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
final = json.loads((ROOT / "runs/g2e/results.json").read_text())

arms = [
    ("V1", "v1", "#9ca3af"),
    ("V2", "v2", "#3b82f6"),
    ("V2H", "v2h", "#60a5fa"),
    ("V3b", "v3b", "#f59e0b"),
    ("V3b-sup", "v3b_sup", "#fbbf24"),
    ("V3b-EMA", "v3b_ema", "#d97706"),
    ("V3b-res", "v3b_residual", "#b45309"),
    ("V3b-comb", "v3b_combined", "#92400e"),
    ("Oracle", "oracle", "#10b981"),
]

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), layout="constrained")
rng = np.random.default_rng(0)


def panel(ax, key, title, ylabel):
    means, stds = [], []
    for i, (label, kind, colour) in enumerate(arms):
        runs = final[kind]["runs"]
        vals = np.array([r[key] for r in runs], dtype=float)
        means.append(vals.mean())
        stds.append(vals.std(ddof=0))
        xs = i + rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter(xs, vals, s=25, color=colour, edgecolor="black",
                   linewidth=0.6, zorder=3)
    xs = np.arange(len(arms))
    ax.bar(xs, means, yerr=stds, color=[a[2] for a in arms], alpha=0.45,
           edgecolor="black", linewidth=0.8, capsize=4, zorder=2)
    for i, m in enumerate(means):
        ax.text(i, m, f"{m:.3f}", ha="center", va="bottom", fontsize=8,
                fontweight="bold")
    ax.set_xticks(xs)
    ax.set_xticklabels([a[0] for a in arms], fontsize=8, rotation=30, ha="right")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_ylabel(ylabel)


panel(axes[0], "force_mae", "Force prediction", "Force MAE (lower is better)")
panel(axes[1], "rollout_drift", "Rollout stability", "Normalised drift (lower is better)")

# state probe R2
ax = axes[2]
means, stds = [], []
for i, (label, kind, colour) in enumerate(arms):
    runs = final[kind]["runs"]
    vals = [r["state_r2"] for r in runs if r["state_r2"] is not None]
    if vals:
        v = np.array(vals, dtype=float)
        means.append(v.mean())
        stds.append(v.std(ddof=0))
        xs = i + rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter(xs, vals, s=25, color=colour, edgecolor="black",
                   linewidth=0.6, zorder=3)
    else:
        means.append(0.0)
        stds.append(0.0)
xs = np.arange(len(arms))
ax.bar(xs, means, yerr=stds, color=[a[2] for a in arms], alpha=0.45,
       edgecolor="black", linewidth=0.8, capsize=4, zorder=2)
for i, m in enumerate(means):
    if m != 0.0:
        ax.text(i, m, f"{m:.2f}", ha="center", va="bottom", fontsize=8,
                fontweight="bold")
ax.set_xticks(xs)
ax.set_xticklabels([a[0] for a in arms], fontsize=8, rotation=30, ha="right")
ax.set_title("State probe R²", fontsize=11, fontweight="bold")
ax.set_ylabel("R² (higher is better)")
ax.set_ylim(0, 1)

fig.suptitle("G2e: latent state vs stateless history baseline", fontsize=13,
             fontweight="bold")
out = ROOT / "docs/07-delivery/figures/g2e-results.png"
fig.savefig(out, dpi=150, facecolor="white")
print(f"wrote {out}")
