---
status: draft
confidence: medium
last_verified: 2026-11-09
depends_on: [05-g0-foundations-result.md, 06-g1-g2-design-questions.md]
---

# G1 and G2 — results

## G1: does the loop close?

**Result: pass.** V1 (direct propagator) trained on the harmonic oracle recovers the
force field to force-MAE **0.0019** (threshold: < 0.01). Training loss drops to
~1e-6 by step 2000 and stays there. One command, one config, one metric table.

| Metric | Value | Threshold | Pass? |
|---|---|---|---|
| Force MAE (held-out) | 0.0019 | < 0.01 | yes |
| Training loss (final) | ~1e-6 | — | — |
| Steps to convergence | ~2000 | — | — |

**What this proves.** The full pipeline works: config → data generation → training →
evaluation → metrics.json. Seeding, logging, checkpointing all function. The SPH
perception operators (via the CPU shim) integrate correctly into an autograd
training loop. V1 can learn a known force field.

**Plain words.** We built a small practice problem — a ball on a spring, where
the right answer is known exactly. We trained our model to predict the spring's
force. It learned it to within 0.2% error. That means the training machinery
works end to end, and we can trust numbers from later experiments.

## G2: does state help?

**Result: negative (preliminary).** V2 (stateless energy) outperforms V3b (latent
state) on a time-varying harmonic oscillator. State tracking was confirmed
(latent dimensions correlate with k(t) at r ≈ 0.6), but it did not translate to
better energy prediction.

| Metric | V2 (stateless) | V3b (latent) | Winner |
|---|---|---|---|
| Energy MAE (held-out) | **0.0114** | 0.2630 | V2 |
| Rollout drift | **0.0166** | 0.3690 | V2 |
| Training loss (final) | 0.0008 | 0.0849 | V2 |
| Latent–k(t) correlation | n/a | r ≈ 0.6 | tracked but unhelpful |

**World.** Harmonic oscillator with k(t) = 1.0 + 0.3·sin(0.1·t). k ranges from
1.0 to ~1.14 over a 500-step trajectory. Held-out world uses freq 0.15 and
phase 0.5.

**What this suggests (inference).** Two candidate explanations:

1. **Optimization, not architecture.** V3b trains sequentially (h evolves
   step-by-step), which is harder to optimize than V2's batched training. The
   latent state tracks k(t) but the energy network doesn't exploit it well.
2. **The world is too easy.** V2 learns the average k (≈1.0) and the variation
   is small (±0.14). V3b's tracking doesn't reduce error enough to matter.

**What would change this result.**

- Longer training for V3b (sequential training is slow; 3000 steps may be
  insufficient).
- A world where the hidden variable has a larger effect (e.g., barrier height
  variation of 0.5, not 0.3).
- A non-conservative world (friction, driving) where state is strictly
  necessary, not just helpful.
- Checking whether V3b's latent state, when frozen to the true k(t), recovers
  V2's performance (ablation).

**Plain words.** We asked: does giving each particle a "memory" help it predict
a spring whose stiffness slowly changes over time? The memory *did* track the
changing stiffness (we can see it in the numbers). But the memory version
predicted worse overall than the version with no memory at all. The memory was
working but not helping — like a student who takes notes but doesn't use them on
the exam. Before concluding that memory is useless, we need to check whether
the problem is the memory itself or just that we didn't train it long enough.

## Open questions

- Is V3b's underperformance due to optimization (fixable) or architecture
  (fundamental)? A longer run and a learning-rate sweep would separate them.
- Does V3b win on a non-conservative world where state is strictly necessary?
- Should G2 use direct force prediction (V1-style) instead of energy, to
  allow non-conservative forces?

## What would change this document

- A V3b run matching or beating V2 on energy MAE after hyperparameter tuning.
- A non-conservative world where V2 cannot fit at all (state becomes necessary).
- Evidence that V3b's latent state, when probed, does not actually track the
  hidden variable (would mean the correlation is spurious).

## Sources

1. Project measurements, 2026-11-09: `runs/v1_harmonic/seed0/metrics.json`,
   `runs/v2_harmonic_tv/seed0/metrics.json`,
   `runs/v3b_harmonic_tv/seed0/metrics.json`.
2. Code: `npa/train/loop.py`, `npa/data/synthetic.py`, `npa/models/v2_energy.py`,
   `npa/models/v3b_latent.py`.