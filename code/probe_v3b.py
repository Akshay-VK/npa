"""Probe: does V3b's latent state track the time-varying spring constant k(t)?"""

import sys
import torch
import numpy as np

sys.path.insert(0, "/mnt/d/dev/ai/experiments/npa")
from npa.models.v3b_latent import LatentEnergyModel
from npa.data.synthetic import make_world, harmonic_trajectory

# Load trained model
model = LatentEnergyModel(hidden=32, latent=8)
ckpt = torch.load("/mnt/d/dev/ai/experiments/npa/runs/v3b_harmonic_tv/seed0/ckpt.pt" if False else None, map_location="cpu") if False else None
# Just retrain quickly or load from checkpoint (none saved). Re-train is fast.
import yaml
config = yaml.safe_load(open("/mnt/d/dev/ai/experiments/npa/configs/v3b_harmonic_tv.yaml"))
from npa.train.loop import train
run = train(config, model, data_kind="harmonic_tv")

# Now probe
world = make_world("harmonic_tv", seed=0, held_out=False)
xs, vs, Es = harmonic_trajectory(world, 500, seed=0)
model.eval()
hs = []
h = torch.zeros(model.latent)
with torch.no_grad():
    for t in range(500):
        xt = xs[t].unsqueeze(0).unsqueeze(-1).float()
        _ = model.energy(xt, h.unsqueeze(0))
        h = model.step_state(xt, torch.zeros(1, 1), h.unsqueeze(0)).squeeze(0)
        hs.append(h.numpy().copy())
hs = np.array(hs)
ks = np.array([world.k(t * 0.01) for t in range(500)])

# Correlation between each latent dimension and k(t)
print("\nCorrelation of each latent dim with k(t):")
for d in range(hs.shape[1]):
    r = np.corrcoef(hs[:, d], ks)[0, 1]
    print(f"  dim {d}: r = {r:.4f}")
print(f"\nk(t) range: [{ks.min():.3f}, {ks.max():.3f}]")
print(f"latent std across time: {hs.std(axis=0).round(3)}")