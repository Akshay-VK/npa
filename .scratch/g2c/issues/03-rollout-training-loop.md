# 03: Rollout training loop

**What to build:** `npa/train/rollout.py` — trains NPA on rollout MSE (predicted vs target trajectory over N steps). Config-driven, checkpointing, metrics. Backprop through multiple Euler steps with gradient clipping.

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] `python -m npa train configs/g2c_v1.yaml` produces a trained model + metrics.json
- [ ] Gradient clipping prevents explosion
- [ ] Checkpoint saved and reloadable
