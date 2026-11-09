"""G0 inference reproduction: load the authors' lizard checkpoint on CPU and
roll it out. This is the cheapest possible check that the official model,
weights and update rule are wired up correctly.

    python g0_infer.py [--n 4096] [--steps 300] [--render-every 5]
"""

import argparse
import os
import time

import numpy as np
import torch
from PIL import Image

import npa_bruteforce

npa_bruteforce.install()

from models.npa import NPA, Pool, step_euler  # noqa: E402
from sphops import HashGrid  # noqa: E402
from utils.splatting import splat_particles  # noqa: E402

OUT = os.path.expanduser("~/npa-work/runs/g0-infer")


def render(x, s, img_size=256):
    color = (s[..., -3:] + 0.5).clamp(0, 1)
    rgba = splat_particles(x[0], color[0], img_size=img_size, sigma=0.5, y_up=True)
    return rgba[..., :3].clamp(0, 1).cpu().numpy()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=4096)
    p.add_argument("--steps", type=int, default=300)
    p.add_argument("--render-every", type=int, default=10)
    p.add_argument("--threads", type=int, default=int(os.environ.get("NPA_THREADS", "16")))
    args = p.parse_args()

    torch.set_num_threads(args.threads)
    os.makedirs(OUT, exist_ok=True)

    ckpt_path = os.path.join(
        os.environ.get("NPA_DIR", os.path.expanduser("~/npa-work/vendor/NPA")),
        "data", "pretrained", "lizard.pth",
    )
    ckpt = torch.load(ckpt_path, map_location="cpu")
    model = NPA(spatial_dims=2, state_dims=16, hidden_dims=128, eps0=0.1, alpha=0.5)
    model.load_state_dict(ckpt)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"loaded {ckpt_path} | params={n_params}")

    grid = HashGrid(
        dim=2, boundary="clamped", mode="grid", grid_size=(16, 16),
        eps=0.1, num_particles=args.n, batch_size=1, max_particles_per_block=32,
    )
    pool = Pool(
        device=torch.device("cpu"), pool_size=1, state_dims=16,
        num_particles=args.n, sigma=0.2, spatial_dims=2,
        seed_mode="uniform_circle", random_seed=42,
    )

    frames = []
    t0 = time.perf_counter()
    with torch.no_grad():
        x, s = pool.seed_generator(1)
        for k in range(args.steps):
            step_n = min(2 ** (k // 30), 8)
            for _ in range(step_n):
                x, s, _ = step_euler(model, x, s, grid)
            if k % args.render_every == 0 or k == args.steps - 1:
                img = (render(x, s) * 255).astype(np.uint8)
                frames.append(img)
                Image.fromarray(img).save(os.path.join(OUT, f"frame_{k:04d}.png"))
                print(f"step {k:4d} | {time.perf_counter()-t0:7.1f}s total")
    dt = time.perf_counter() - t0

    Image.fromarray(frames[-1]).save(os.path.join(OUT, "final.png"))
    # contact sheet: first / middle / last
    picks = [frames[0], frames[len(frames) // 2], frames[-1]]
    sheet = np.concatenate(picks, axis=1)
    Image.fromarray(sheet).save(os.path.join(OUT, "contact_sheet.png"))

    try:
        import imageio.v3 as iio
        iio.imwrite(os.path.join(OUT, "rollout.gif"), frames, duration=0.1, loop=0)
    except Exception as e:  # noqa: BLE001
        print("gif skipped:", e)

    print(f"done | {args.steps} steps in {dt:.1f}s | {dt/args.steps:.3f}s/step")
    print(f"artefacts: {OUT}")


if __name__ == "__main__":
    main()
