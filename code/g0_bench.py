"""G0 benchmark: where does the brute-force CPU port run out of headroom?

Run one N per process so peak RSS is clean:
    python g0_bench.py --n 512 [--batch 1] [--steps 20]
"""

import argparse
import json
import os
import resource
import time

import torch

import npa_bruteforce

npa_bruteforce.install()

from models.npa import NPA, Pool, step_euler  # noqa: E402
from sphops import HashGrid  # noqa: E402


def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=512)
    p.add_argument("--batch", type=int, default=1)
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--train", action="store_true", help="also time one backward pass")
    p.add_argument("--threads", type=int, default=int(os.environ.get("NPA_THREADS", "16")))
    args = p.parse_args()

    torch.set_num_threads(args.threads)

    grid = HashGrid(
        dim=2, boundary="clamped", mode="grid", grid_size=(16, 16),
        eps=0.1, num_particles=args.n, batch_size=args.batch,
        max_particles_per_block=32,
    )
    model = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
    pool = Pool(
        device=torch.device("cpu"), pool_size=8, state_dims=16,
        num_particles=args.n, sigma=0.2, spatial_dims=2,
        seed_mode="uniform_circle", random_seed=42,
    )
    x, s, _ = pool.sample(args.batch)

    t0 = time.perf_counter()
    with torch.no_grad():
        for _ in range(args.steps):
            x, s, _ = step_euler(model, x, s, grid, update_prob=0.5)
    dt = (time.perf_counter() - t0) / args.steps

    out = {
        "n": args.n, "batch": args.batch, "threads": args.threads,
        "sec_per_step": round(dt, 4),
        "peak_rss_mb": round(peak_mb(), 1),
    }

    if args.train:
        model.zero_grad(set_to_none=True)
        x, s, _ = pool.sample(args.batch)
        t0 = time.perf_counter()
        x2, s2, _ = step_euler(model, x, s, grid, update_prob=0.5)
        loss = (s2 ** 2).mean() + (x2 ** 2).mean()
        loss.backward()
        out["sec_per_train_step"] = round(time.perf_counter() - t0, 4)
        out["peak_rss_mb"] = round(peak_mb(), 1)

    print(json.dumps(out))
    with open(os.path.expanduser("~/npa-work/logs/g0_bench.jsonl"), "a") as f:
        f.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
