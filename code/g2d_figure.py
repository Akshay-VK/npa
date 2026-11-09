"""G2d figure: force MAE, rollout drift, and state-probe R2 by arm."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
final = json.loads((ROOT / "runs/g2d_final/results.json").read_text())
v1 = json.loads((ROOT / "runs/g2d_v1_final/results.json").read_text())
v1_runs = v1["v1"]["runs"]

arms = [
    ("V1\ndirect", v1_runs, "#9ca3af"),
    ("V2\nstateless", final["v2"]["runs"], "#3b82f6"),
    ("V3b\nlatent", final["v3b"]["runs"], "#f59e0b"),
    ("Oracle\ntrue phase", final["oracle"]["runs"], "#10b981"),
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

fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.7), layout="constrained")
rng = np.random.default_rng(0)


def panel(ax, key, title, ylabel, ylim=None):
    means, stds = [], []
    for i, (_, runs, colour) in enumerate(arms):
        vals = np.array([r[key] for r in runs], dtype=float)
        means.append(vals.mean())
        stds.append(vals.std(ddof=0))
        xs = i + rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter(xs, vals, s=26, color=colour, edgecolor="black",
                   linewidth=0.5, zorder=3)
    xs = np.arange(len(arms))
    ax.bar(xs, means, yerr=stds, color=[a[2] for a in arms], alpha=0.45,
           edgecolor="black", linewidth=0.7, capsize=4, zorder=2)
    for i, m in enumerate(means):
        ax.text(i, m + max(stds) * 0.08, f"{m:.3f}", ha="center", va="bottom",
                fontsize=8.5, fontweight="bold")
    ax.set_xticks(xs)
    ax.set_xticklabels([a[0] for a in arms], fontsize=8.5)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.axhline(0, color="black", linewidth=0.6, zorder=1)


panel(axes[0], "force_mae", "Force prediction", "Force MAE (lower is better)")
panel(axes[1], "rollout_drift", "Rollout stability",
      "Normalised drift (lower is better)")

# State probe R2 per seed.
r2 = np.array([r["state_r2"] for r in final["v3b"]["runs"]], dtype=float)
axes[2].bar([0], [r2.mean()], color="#f59e0b", alpha=0.45, edgecolor="black",
            linewidth=0.7, width=0.55, zorder=2)
axes[2].scatter(rng.uniform(-0.12, 0.12, len(r2)), r2, s=26, color="#f59e0b",
                edgecolor="black", linewidth=0.5, zorder=3)
axes[2].axhline(1.0, color="#6b7280", linestyle="--", linewidth=0.8)
axes[2].text(0.03, 0.97, "perfect", va="top", fontsize=8, color="#6b7280")
axes[2].set_xticks([0])
axes[2].set_xticklabels(["V3b"], fontsize=9)
axes[2].set_xlim(-0.6, 0.6)
axes[2].set_ylim(0, 1.05)
axes[2].set_title("What the state carries")
axes[2].set_ylabel("Phase variance explained (R²)")
axes[2].text(0.03, r2.mean() + 0.04, f"{r2.mean():.3f}", fontsize=8.5,
             fontweight="bold")

fig.suptitle("G2d: latent state on a hidden-phase world (3 seeds, 1,200 steps)",
             fontsize=12, fontweight="bold")
fig.text(0.5, -0.02,
         "Bars: mean. Dots: individual seeds. Force MAE is measured at true "
         "positions with the rollout state. Lower is better on both error panels.",
         ha="center", fontsize=7.5, color="#4b5563")

out = ROOT / "docs/07-delivery/figures/g2d-results.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
print(f"wrote {out}")
