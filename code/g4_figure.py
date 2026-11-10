"""G4 figure: barrier MAE and reaction energy MAE from a metrics file."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap_path = ROOT / "runs/g4_small/metrics.json"
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", type=str, default=str(ap_path))
    ap.add_argument("--out", type=str, default=str(ROOT / "docs/07-delivery/figures/g4-pipeline.png"))
    args = ap.parse_args()

    m = json.loads(Path(args.metrics).read_text())
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["barrier MAE", "reaction energy MAE"]
    vals = [m["barrier_mae_kcal"], m["reaction_energy_mae_kcal"]]
    ax.bar(labels, vals, color=["#3b82f6", "#f59e0b"])
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontweight="bold")
    ax.set_ylabel("MAE (kcal/mol)")
    ax.set_title("G4 pipeline (small slice, 10 epochs)")
    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
