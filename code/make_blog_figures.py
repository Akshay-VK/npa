"""Generate blog-ready hero and infographic figures."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "docs" / "07-delivery" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def hero():
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(8, 4.5), dpi=150,
                                   gridspec_kw={"width_ratios": [1.5, 1.0]})
    # Left: barrier comparison
    conds = ["Cheap labels\nCCSD(T)/VDZ", "MP2 control\nMP2/cc-pVTZ"]
    vals = [9.683, 13.023]
    errs = [0.037, 0.270]
    colors = ["#10b981", "#dc2626"]
    x = np.arange(len(conds))
    ax.bar(x, vals, yerr=errs, capsize=4, color=colors, alpha=0.85,
           edgecolor="black", linewidth=0.8, width=0.6)
    for xi, v, e in zip(x, vals, errs):
        ax.text(xi, v + e + 0.15, f"{v:.3f} ± {e:.3f}", ha="center",
                va="bottom", fontsize=9, fontweight="bold")
    ax.axhline(10.010, color="#1f2937", linestyle="-", linewidth=1.6, zorder=3)
    ax.text(1.55, 10.010 + 0.12, "reference 10.010", color="#1f2937",
            fontsize=9, ha="right", va="bottom", fontweight="bold")
    # gate band
    ax.axhspan(10.010 - 1.5, 10.010 + 1.5, color="#3b82f6", alpha=0.08, zorder=0)
    ax.text(0.02, 10.010 - 1.5 + 0.05, "gate band ±1.5", color="#3b82f6",
            fontsize=8, ha="left", va="bottom", transform=ax.get_yaxis_transform())
    ax.set_xticks(x)
    ax.set_xticklabels(conds, fontsize=9)
    ax.set_ylabel("Predicted barrier (kcal/mol)")
    ax.set_ylim(8.5, 14.0)
    ax.set_title("G3 barrier: cheap labels pass, MP2 control fails", fontsize=11,
                 fontweight="bold")
    # verdict annotations
    ax.text(0, 9.0, "PASS\nerr 0.327", ha="center", va="center", fontsize=9,
            fontweight="bold", color="#10b981",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#10b981"))
    ax.text(1, 12.4, "FAIL\nerr 3.013", ha="center", va="center", fontsize=9,
            fontweight="bold", color="#dc2626",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#dc2626"))

    # Right: gate checklist
    ax2.axis("off")
    ax2.set_title("G3 gate (3/3)", fontsize=12, fontweight="bold")
    lines = [
        ("Barrier error", "0.327", "< 1.5", "PASS", "#10b981"),
        ("MP2 control", "3.013", "> 1.5 (must fail)", "FAIL (as designed)", "#dc2626"),
        ("Rotation invariance", "1.1e-5", "< 1e-4 eV", "PASS", "#10b981"),
        ("Dissociation (20 Å)", "0.031", "flat", "PASS", "#10b981"),
    ]
    y = 0.85
    for name, val, thr, verdict, col in lines:
        ax2.text(0.05, y, name, fontsize=9, fontweight="bold", transform=ax2.transAxes)
        ax2.text(0.05, y - 0.06, f"{val}  ({thr})", fontsize=8, color="#4b5563",
                 transform=ax2.transAxes)
        ax2.text(0.95, y - 0.03, verdict, fontsize=9, fontweight="bold", color=col,
                 ha="right", transform=ax2.transAxes)
        y -= 0.20
    ax2.text(0.05, 0.02, "Reference: CCSD(T)/cc-pVTZ = 10.010\n"
                          "Cheap: CCSD(T)/cc-pVDZ (never sees cc-pVTZ)\n"
                          "3 seeds, MLP 4,482 params",
             fontsize=8, color="#6b7280", transform=ax2.transAxes)
    fig.suptitle("NPA: H + H2 -> H2 + H barrier from cheap labels",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = FIG / "blog-hero.png"
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


def infographic():
    fig = plt.figure(figsize=(8, 10), dpi=150)
    gs = fig.add_gridspec(4, 1, hspace=0.35)
    fig.suptitle("NPA project: from reproduction to chemistry gate",
                 fontsize=15, fontweight="bold", y=0.98)

    # G0
    ax = fig.add_subplot(gs[0])
    ax.set_title("G0  Reproduction (NPA on CPU)", fontsize=12, fontweight="bold", loc="left")
    arms = ["Trained\n1024", "Trained\n4096", "Random ctrl\n1024"]
    vals = [0.674, 0.869, 0.124]
    colors = ["#3b82f6", "#3b82f6", "#9ca3af"]
    x = np.arange(len(arms))
    ax.bar(x, vals, color=colors, alpha=0.85, edgecolor="black", linewidth=0.8)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.02, f"{v:.3f}", ha="center", va="bottom", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(arms, fontsize=9)
    ax.set_ylabel("support IoU")
    ax.set_ylim(0, 1.0)
    ax.text(0.98, 0.5, "Official NPA runs on CPU\nvia brute-force SPH kernels.\nReproduction is real, not rendering.",
            transform=ax.transAxes, ha="right", va="center", fontsize=9, color="#4b5563")

    # G2e
    ax = fig.add_subplot(gs[1])
    ax.set_title("G2e  Latent state: dynamics improve, state does not track phase",
                 fontsize=12, fontweight="bold", loc="left")
    arms = ["V2\nstateless", "V2H\nhistory", "V3b-combined", "Oracle"]
    vals = [1.123, 0.887, 0.639, 0.384]
    colors = ["#9ca3af", "#9ca3af", "#f59e0b", "#10b981"]
    x = np.arange(len(arms))
    ax.bar(x, vals, color=colors, alpha=0.85, edgecolor="black", linewidth=0.8)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.02, f"{v:.3f}", ha="center", va="bottom", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(arms, fontsize=9)
    ax.set_ylabel("force MAE")
    ax.set_ylim(0, 1.3)
    ax.text(0.98, 0.6, "Drift: 0.079 vs 0.115\nState probe R2 = 0.302 (need >0.5)\nState is a regulariser, not a phase tracker.",
            transform=ax.transAxes, ha="right", va="center", fontsize=9, color="#4b5563")

    # G3
    ax = fig.add_subplot(gs[2])
    ax.set_title("G3  Chemistry gate: H + H2 -> H2 + H barrier",
                 fontsize=12, fontweight="bold", loc="left")
    conds = ["Reference\nCCSD(T)/VTZ", "Cheap model", "MP2 control"]
    vals = [10.010, 9.683, 13.023]
    errs = [0, 0.037, 0.270]
    colors = ["#1f2937", "#10b981", "#dc2626"]
    x = np.arange(len(conds))
    ax.bar(x, vals, yerr=errs, capsize=4, color=colors, alpha=0.85, edgecolor="black",
           linewidth=0.8)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.15, f"{v:.3f}", ha="center", va="bottom", fontweight="bold")
    ax.axhspan(10.010 - 1.5, 10.010 + 1.5, color="#3b82f6", alpha=0.08)
    ax.set_xticks(x)
    ax.set_xticklabels(conds, fontsize=9)
    ax.set_ylabel("barrier (kcal/mol)")
    ax.set_ylim(8, 14)
    ax.text(0.98, 0.5, "Error 0.327 < 1.5: PASS\nMP2 control 3.013: FAIL (as designed)\nRotation 1.1e-5, dissociation 0.031: PASS",
            transform=ax.transAxes, ha="right", va="center", fontsize=9, color="#4b5563")

    # G4
    ax = fig.add_subplot(gs[3])
    ax.set_title("G4  Transition1x pipeline (plumbing works, no real numbers yet)",
                 fontsize=12, fontweight="bold", loc="left")
    arms = ["10 ep\nh32", "50 ep\nh32", "50 ep\nh128"]
    vals = [116.6, 108.6, 99.4]
    colors = ["#93c5fd", "#60a5fa", "#3b82f6"]
    x = np.arange(len(arms))
    ax.bar(x, vals, color=colors, alpha=0.85, edgecolor="black", linewidth=0.8)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 1.5, f"{v:.1f}", ha="center", va="bottom", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(arms, fontsize=9)
    ax.set_ylabel("barrier MAE (kcal/mol)")
    ax.set_ylim(0, 130)
    ax.text(0.98, 0.5, "14 tests pass on mock HDF5.\nReal-data slice only (3/2/8 formulas).\nNot a chemistry result yet.",
            transform=ax.transAxes, ha="right", va="center", fontsize=9, color="#4b5563")

    out = FIG / "blog-infographic.png"
    fig.savefig(out, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    hero()
    infographic()
