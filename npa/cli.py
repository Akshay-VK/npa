"""Entry point: python -m npa train|eval|bench CONFIG [--seed N]."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    p = argparse.ArgumentParser(prog="npa")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train")
    t.add_argument("config")
    t.add_argument("--seed", type=int, default=0)
    e = sub.add_parser("eval")
    e.add_argument("run_dir")
    b = sub.add_parser("bench")
    b.add_argument("config")
    args = p.parse_args()
    print(f"npa {args.cmd}: not implemented yet (v0.0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())