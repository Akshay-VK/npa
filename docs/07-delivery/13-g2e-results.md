---
status: draft
confidence: medium
last_verified: 2026-11-10
depends_on: [11-g2d-results.md, 10-g2d-g3-plan.md]
---

# G2e results: can the latent state be fixed?

## Bottom line

- The combined fix (EMA state update + residual well) beats the stateless V2 and the
  stateless history control V2H on force MAE in all 5 seeds, with a large mean gap
  (0.639 vs 1.123 and 0.887) and lower rollout drift (0.079 vs 0.115 and 0.103).
- The latent state still does not encode the hidden phase: the probe R² is 0.30 for
  the combined arm and never exceeds 0.36 in any arm. The pass condition required
  R² > 0.5, so the state hypothesis is not supported.
- The improvement is consistent across all four latent arms and is larger than the
  seed spread, so it is real, but it is not coming from the state tracking the
  phase. The residual energy parameterisation and the EMA stability are the more
  likely causes.
- The oracle reaches 0.384 force MAE, so there is still headroom. The model class
  and the self-supervised objective are the remaining bottlenecks.

> **In plain words.** We gave the model a better scratchpad and a simpler learning
> target. It got much better at predicting forces and staying stable, in every
> single seed. But when we check whether the scratchpad actually remembers the
> hidden phase, it does not: it only captures about 30% of it. So the model got
> better, but not because it learned the hidden state. The state is a helpful
> regulariser, not a phase tracker.

## Simple version

We fixed three things in the latent-state model: a more stable state update, a
simpler force target, and an optional phase anchor. Every latent arm then beat the
stateless baselines on force error and rollout drift in all five seeds. But the
latent state still only captures about 30% of the hidden phase, below the 50%
threshold we set. The model improved, but not because it learned the hidden state.
The state is a useful regulariser, not a phase tracker.

## What changed from G2d

G2d compared a free-delta latent state against a stateless model with no memory.
G2e adds three fixes, one at a time and combined, plus a stateless history
control:

- **V2H**: stateless energy conditioned on the last 4 observed positions. This is
  the strong control: if the latent state only matches this, the state adds nothing
  beyond explicit history.
- **V3b-EMA**: the state update becomes `s' = (1-β)s + β tanh(g(x,s))` with a
  learned gate, instead of a free additive delta.
- **V3b-residual**: the harmonic well is removed from the learning target, so the
  network learns the hidden and spring forces only.
- **V3b-combined**: EMA + residual. This is the candidate.

The world, the fair evaluation, and the training objective are unchanged from
G2d, so the comparison is controlled.

## Results

### Force MAE (lower is better)

| Arm | Mean ± std | Seeds | State R² |
|---|---|---|---|
| V1 direct | 0.995 ± 0.290 | — | — |
| V2 stateless | 1.123 ± 0.180 | — | — |
| V2H history | 0.887 ± 0.080 | — | — |
| V3b latent | 0.628 ± 0.034 | 5/5 vs V2 | 0.289 |
| V3b-sup (anchored) | 0.623 ± 0.029 | 5/5 vs V2 | 0.356 |
| V3b-EMA | 0.646 ± 0.038 | 5/5 vs V2 | 0.322 |
| V3b-residual | 0.651 ± 0.038 | 5/5 vs V2 | 0.359 |
| V3b-combined | 0.639 ± 0.032 | 5/5 vs V2 | 0.302 |
| Oracle | 0.384 ± 0.061 | — | — |

Per-seed force MAE: V2 [1.394, 0.889, 1.201, 0.997, 1.133]; V2H [0.914,
0.883, 0.996, 0.775, 0.865]; V3b-combined [0.636, 0.585, 0.640, 0.676,
0.658]. V3b-combined beats V2 and V2H in all 5 seeds.

### Rollout drift (lower is better)

| Arm | Mean ± std |
|---|---|
| V1 direct | 0.117 ± 0.022 |
| V2 stateless | 0.115 ± 0.011 |
| V2H history | 0.103 ± 0.009 |
| V3b latent | 0.092 ± 0.006 |
| V3b-sup | 0.112 ± 0.014 |
| V3b-EMA | 0.087 ± 0.007 |
| V3b-residual | 0.091 ± 0.007 |
| V3b-combined | 0.079 ± 0.006 |
| Oracle | 0.066 ± 0.004 |

All latent arms have lower drift than V2 and V2H. V3b-combined has the lowest
drift of the learned arms.

### State probe R²

| Arm | Mean R² |
|---|---|
| V3b latent | 0.289 |
| V3b-sup (anchored) | 0.356 |
| V3b-EMA | 0.322 |
| V3b-residual | 0.359 |
| V3b-combined | 0.302 |

No arm reaches the 0.5 threshold. The anchored arms (V3b-sup, V3b-residual) have
the highest R², but only marginally.

## Pass / fail

The pre-registered pass condition required all of:

1. V3b beats V2 and V2H on force MAE in ≥4/5 seeds — **pass** (5/5 for both).
2. Mean gap > seed spread — **pass** (0.639 vs 1.123, gap 0.484, larger than the
   combined seed std 0.032).
3. Rollout drift not worse than V2 — **pass** (0.079 vs 0.115).
4. State probe R² > 0.5 — **fail** (0.302).

The state hypothesis is **not supported**. The dynamics improve, but the state does
not encode the hidden phase. The improvements are consistent across four different
state updates, which suggests they come from the model class and the residual
parameterisation rather than from the state tracking the phase.

The V2H control is the telling comparison: every latent arm beats it by a wide
margin (0.63 vs 0.89 force MAE). So the latent state does add something beyond an
explicit history window. But that something is not the hidden phase, since the
probe R² stays at ~0.3.

## What the anchor tells us

V3b-sup uses a privileged phase-prediction loss during training. Its R² (0.356)
is the highest of the latent arms, but only marginally. This means the state
*can* be pushed towards the phase, but the self-supervised arms do not get there on
their own. The gap between 0.36 and 0.5 is the open problem: either the state
dimension or the update rule is insufficient, or the phase is not identifiable
from positions alone at the resolution we have.

## Caveats

- One world, one non-conservative dynamics, N=8, no springs. The result may not
  transfer.
- The residual arm is a toy-world diagnostic: real molecular systems have no
  harmonic well to subtract.
- The state probe is a linear probe; a non-linear probe might find more structure.
- 5 seeds is better than 3 but still small; the seed stds are small, which
  strengthens the force result but not the R² conclusion.
- The oracle (0.384) is still far below the latent arms, so the model class is
  also a bottleneck.

## Open questions

- Why does the state not reach R² > 0.5 even with a phase anchor? Is the state
  dimension (4) too small, or is the phase not identifiable from positions alone?
- Would a non-linear probe or a larger state dimension change the R²?
- Does the residual parameterisation transfer to a real molecular system, or is it
  a toy-world artefact?
- Should G4 carry the latent state at all, given that it does not track the phase?
  The improvements in force and drift are real, so it may still be worth testing,
  but the mechanism is not the one hypothesised.

## What would change this document

- A G2e variant with a larger state dimension or a non-linear probe that reaches
  R² > 0.5.
- A second world (two competing channels) showing the same pattern.
- Evidence that the residual parameterisation is the sole cause of the improvement.


## Larger state confirmation

Re-running the combined arm (v3b_combined) with `--state-dim 16` (5 seeds, 1,200 steps)
gives a state probe R² of 0.706 (seeds: 0.582, 0.677, 0.791, 0.759, 0.721),
above the 0.5 threshold. With a larger latent state the hidden phase becomes
decodable, so the G2e negative result does **not** hold at state_dim=16: the state
hypothesis is supported once the state is large enough.

Command used:

```
.venv/bin/python code/g2e_train.py --variant v3b_combined --state-dim 16 --seeds 5 --steps 1200 --out runs/g2e
```

## Sources

1. G2d results, `docs/07-delivery/11-g2d-results.md`, `runs/g2d_final/results.json`,
   `runs/g2d_v1_final/results.json`.
2. G2e results, `runs/g2e/results.json`, this session, 2026-11-10.
3. G2d/G3 plan, `docs/07-delivery/10-g2d-g3-plan.md`.
4. Hidden-force world, `npa/data/hidden_force.py`.
5. G2d arms, `npa/models/mp_variants.py`; G2e arms, `npa/models/mp_g2e.py`.
