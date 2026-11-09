"""Entry point: python -m npa train|eval|bench CONFIG [--seed N]."""

from __future__ import annotations

import argparse
import sys

import yaml

from npa.data.synthetic import make_world
from npa.models.v0_oracle import HarmonicOracle
from npa.models.v1_direct import DirectPropagator
from npa.models.v2_energy import EnergyModel
from npa.models.v3b_latent import LatentEnergyModel
from npa.train.loop import train


def build_model(cfg: dict):
    kind = cfg.get("model", {}).get("kind", "v1_direct")
    hidden = cfg.get("model", {}).get("hidden", 32)
    latent = cfg.get("model", {}).get("latent", 8)
    if kind == "oracle":
        return HarmonicOracle(k=cfg.get("model", {}).get("k", 1.0))
    if kind == "v1_direct":
        return DirectPropagator(hidden=hidden)
    if kind == "v2_energy":
        return EnergyModel(hidden=hidden)
    if kind == "v3b_latent":
        return LatentEnergyModel(hidden=hidden, latent=latent)
    raise ValueError(f"unknown model kind: {kind}")


def main() -> int:
    p = argparse.ArgumentParser(prog="npa")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train")
    t.add_argument("config")
    t.add_argument("--seed", type=int, default=None)
    t.add_argument("--out-dir", default="runs")
    e = sub.add_parser("eval")
    e.add_argument("run_dir")
    b = sub.add_parser("bench")
    b.add_argument("config")
    args = p.parse_args()

    if args.cmd == "train":
        with open(args.config) as f:
            config = yaml.safe_load(f)
        if args.seed is not None:
            config["seed"] = args.seed
        config.setdefault("out_dir", args.out_dir)
        config.setdefault("name", args.config.split("/")[-1].replace(".yaml", ""))
        model = build_model(config)
        from npa.data.synthetic import make_world
        world_kind = config.get("world", "harmonic")
        run = train(config, model, data_kind=world_kind)
        print(f"run saved to {run.out_dir}")
        print(f"metrics: {run.metrics}")
        return 0
    if args.cmd == "eval":
        print(f"eval {args.run_dir}: not implemented yet")
        return 0
    if args.cmd == "bench":
        print(f"bench {args.config}: not implemented yet")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())