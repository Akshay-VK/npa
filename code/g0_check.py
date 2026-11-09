"""G0 quantitative check: does the pretrained checkpoint actually assemble the
target morphology, and does a random-init control fail to?

Runs the official update rule on CPU and scores support-IoU against the target
emoji mask. Saves JSON to ~/npa-work/logs/g0_check.json.
"""

import argparse
import json
import os

import numpy as np
import torch

import npa_bruteforce

npa_bruteforce.install()

from models.npa import NPA, Pool, step_euler  # noqa: E402
from sphops import HashGrid  # noqa: E402
from utils.loader import load_target_image  # noqa: E402
from utils.splatting import splat_particles  # noqa: E402

TARGET = os.environ.get(
    "NPA_TARGET", os.path.expanduser("~/npa-work/data/lizard.png")
)
CKPT = os.path.join(
    os.environ.get("NPA_DIR", os.path.expanduser("~/npa-work/vendor/NPA")),
    "data", "pretrained", "lizard.pth",
)


def adaptive_size(num_points, threshold=0.05):
    H = 128
    for _ in range(5):
        img = load_target_image(TARGET, size=[H, H])
        nonzero = int(np.sum(img[..., 3] >= threshold))
        H = int(np.round(np.sqrt(num_points / nonzero) * H))
    return H


def target_mask(H, threshold=0.05):
    img = load_target_image(TARGET, size=[H, H])
    return torch.from_numpy(img[..., 3] >= threshold)


def render_density(x, s, H):
    color = (s[..., -3:] + 0.5).clamp(0, 1)
    rgba = splat_particles(x[0], color[0], img_size=H, sigma=0.5, y_up=True)
    return rgba[..., 3]


def iou(a, b):
    inter = (a & b).sum().item()
    union = (a | b).sum().item()
    return inter / max(union, 1)


def rollout(model, n, steps, grid, pool, H, target, log_every=30):
    out = []
    with torch.no_grad():
        x, s = pool.seed_generator(1)
        for k in range(steps):
            step_n = min(2 ** (k // 30), 8)
            for _ in range(step_n):
                x, s, _ = step_euler(model, x, s, grid)
            if (k + 1) % log_every == 0 or k == 0:
                dens = render_density(x, s, H)
                pred = dens > dens.mean() * 0.5
                out.append({"step": k + 1, "iou": round(iou(pred, target), 4),
                            "coverage": round(pred.float().mean().item(), 4)})
    return out, x, s


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=1024)
    p.add_argument("--steps", type=int, default=120)
    p.add_argument("--threads", type=int, default=int(os.environ.get("NPA_THREADS", "16")))
    p.add_argument("--models", choices=["pretrained", "both"], default="both")
    args = p.parse_args()

    torch.set_num_threads(args.threads)
    H = adaptive_size(args.n)
    target = target_mask(H)
    print(f"N={args.n} target={os.path.basename(TARGET)} render={H}x{H} target_cov={target.float().mean():.3f}")

    grid = HashGrid(
        dim=2, boundary="clamped", mode="grid", grid_size=(16, 16),
        eps=0.1, num_particles=args.n, batch_size=1, max_particles_per_block=32,
    )
    pool = Pool(
        device=torch.device("cpu"), pool_size=1, state_dims=16,
        num_particles=args.n, sigma=0.2, spatial_dims=2,
        seed_mode="uniform_circle", random_seed=42,
    )

    pretrained = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
    pretrained.load_state_dict(torch.load(CKPT, map_location="cpu"))
    pretrained.eval()

    control = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
    control.eval()

    res = {}
    runs = [("pretrained", pretrained)]
    if args.models == "both":
        runs.append(("random_init", control))
    for name, model in runs:
        torch.manual_seed(42)  # same seed cloud for both
        traj, _, _ = rollout(model, args.n, args.steps, grid, pool, H, target)
        res[name] = traj
        print(name, traj[-1])

    out_path = os.path.expanduser(f"~/npa-work/logs/g0_check_n{args.n}.json")
    with open(out_path, "w") as f:
        json.dump({"n": args.n, "target": os.path.basename(TARGET), "H": H,
                   "steps": args.steps, "runs": res}, f, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
