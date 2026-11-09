---
status: draft
confidence: medium
last_verified: 2026-11-09
depends_on: [05-g0-foundations-result.md, 06-g1-g2-design-questions.md]
---

# G1 and G2 — results (updated)

## G1: does the loop close?

**Result: pass.** V1 (direct propagator) trained on the harmonic oracle recovers the
force field to **force-MAE 0.0019** (threshold: < 0.01). Training loss drops to
~1e-6 by step 2000. One command, one config, one metric table.

| Metric | Value | Threshold | Pass? |
|---|---|---|---|
| Force MAE (held-out) | 0.0019 | < 0.01 | yes |
| Training loss (final) | ~1e-6 | — | — |

**Plain words.** The training pipeline works end to end. The model learned a known
force field to 0.2% error. We can trust numbers from later experiments.

## G2: does state help? (restructured: single network, NCA-style)

After restructuring V3b from two networks to a single network (as the user
correctly pointed out, matching NCA/NPA's actual design), the latent state now
tracks the hidden variable almost perfectly — but energy prediction is still
worse than the stateless baseline.

| Metric | V2 (stateless) | V3b (single-net latent) |
|---|---|---|
| Energy MAE (held-out) | **0.0114** | 0.2246 |
| Rollout drift | **0.0166** | 0.2735 |
| Training loss (final) | 0.0008 | 0.0274 |
| Latent–k(t) correlation | n/a | **r ≈ 0.99** (all 8 dims) |

**What changed with the restructure.** The single-network design dramatically
improved state tracking: correlation went from r ≈ 0.6 (two-network, V3b v1) to
r ≈ 0.99 (single-network, V3b v2). The state net and energy net now share
parameters, so the optimizer has a direct path to make the state useful for
energy prediction.

**But energy prediction still loses.** Even with near-perfect state tracking, V3b's
energy MAE (0.225) is 20× worse than V2's (0.011). The gap is in training
efficiency: V2 uses batched random sampling (stable gradients, 3000 steps), while
V3b uses sequential training (noisy gradients, 6 epochs × 3 trajectories).

**Candidate explanations (inference).**

1. **Optimization, not architecture.** Sequential training through time is
   inherently harder. V3b's gradients are noisier and less sample-efficient.
   The state tracks k(t) but the energy network can't exploit it well enough.
2. **The world is too easy.** V2 learns the average k (≈1.05) and the variation
   is modest (±0.15). V3b's tracking doesn't reduce error enough to matter.
3. **State update is unsupervised.** The state net (step_state) has no direct
   loss — it's only trained through the energy loss. The optimizer may not push
   it to be useful for energy prediction.

**What would change this result.**

- Train V3b with more steps or a higher learning rate.
- Add a direct supervision signal for the state (e.g., train h to predict k(t)).
- Use a harder world where V2 cannot approximate the energy (larger k variation).
- Switch V3b to batched training by precomputing h(t) from a frozen state
  update, then training the energy network on (x, h) pairs.

**Plain words.** We rebuilt the "memory" version as a single network (the way
Neural Cellular Automata actually work), and the memory now perfectly tracks the
changing spring stiffness. But the memory version still predicts worse than the
no-memory version. The memory is working — it's just not being used well enough
by the energy prediction. The likely culprit is training: the memory version
trains by watching movies (sequential, noisy) while the no-memory version studies
flashcards (batched, stable). The memory version needs more training or a
different training approach to catch up.

## Open questions

- Is V3b's underperformance due to optimization (fixable with more training)
  or architecture (fundamental)?
- Would batched training (precompute h, then train energy on (x, h) pairs)
  close the gap?
- Does a harder world (larger k variation) make state necessary rather than
  merely helpful?

## What would change this document

- A V3b run matching or beating V2 on energy MAE after hyperparameter tuning.
- Evidence that V3b's latent state, when frozen to the true k(t), recovers
  V2's performance (would isolate the state-tracking from the energy-learning).
- A non-conservative world where V2 cannot fit at all.

## Sources

1. Project measurements, 2026-11-09: `runs/v1_harmonic/seed0/metrics.json`,
   `runs/v2_harmonic_tv/seed0/metrics.json`,
   `runs/v3b_harmonic_tv/seed0/metrics.json`.
2. Code: `npa/train/loop.py`, `npa/data/synthetic.py`,
   `npa/models/v2_energy.py`, `npa/models/v3b_latent.py`.