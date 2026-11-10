"""Slice a small subset of Transition1x.h5 for CPU iteration."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import h5py


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-heavy", type=int, default=7)
    ap.add_argument("--train-formulas", type=int, default=3)
    ap.add_argument("--include-test", action="store_true", default=True)
    args = ap.parse_args()

    with h5py.File(args.input, "r") as src, h5py.File(args.output, "w") as dst:
        data_in = src["data"]
        data_out = dst.create_group("data")
        train_out = dst.create_group("train")
        val_out = dst.create_group("val")
        test_out = dst.create_group("test")

        # pick formulas from train that pass the filter
        def ok_formula(fm):
            grp = data_in[fm]
            rxn = list(grp.keys())[0]
            z = [int(x) for x in grp[rxn]["atomic_numbers"][...]]
            return all(z_i in (1, 6, 7, 8) for z_i in z) and sum(1 for z_i in z if z_i > 1) <= args.max_heavy

        train_formulas = [fm for fm in src["train"].keys() if ok_formula(fm)]
        val_formulas = [fm for fm in src["val"].keys() if ok_formula(fm)]
        test_formulas = [fm for fm in src["test"].keys() if ok_formula(fm)]

        chosen_train = train_formulas[:args.train_formulas]
        chosen_val = val_formulas[:2]
        chosen_test = test_formulas  # all held-out test formulas

        def copy_formula(fm):
            src.copy(f"/data/{fm}", data_out, name=fm)

        for fm in chosen_train + chosen_val + chosen_test:
            copy_formula(fm)

        for fm in chosen_train:
            train_out[fm] = h5py.SoftLink(f"/data/{fm}")
        for fm in chosen_val:
            val_out[fm] = h5py.SoftLink(f"/data/{fm}")
        for fm in chosen_test:
            test_out[fm] = h5py.SoftLink(f"/data/{fm}")

        print(f"train formulas: {len(chosen_train)}")
        print(f"val formulas:   {len(chosen_val)}")
        print(f"test formulas:  {len(chosen_test)}")
        print(f"output: {args.output}")
        print(f"size: {Path(args.output).stat().st_size} bytes")


if __name__ == "__main__":
    from pathlib import Path
    main()
