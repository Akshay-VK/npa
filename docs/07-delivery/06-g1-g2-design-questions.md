---
status: draft
confidence: medium
last_verified: 2026-11-09
depends_on: [01-roadmap-and-kill-criteria.md, 05-g0-foundations-result.md]
---

# G1/G2 design questions

Decisions made before building. Each has a default; override by editing this doc
before the corresponding stage starts.

## Q1. Toy world dimensionality

**Question.** 1D single-particle systems (harmonic, double well) or 2D multi-particle?

**Default.** 1D single-particle for G1 (harmonic) and G2 (double well). 2D multi-particle is
a stretch goal after G2 passes. Reason: a single particle in a known potential is
the cleanest possible test — the oracle answer is exact, and any failure is the
model's fault, not the world's.

**Would change if.** The G2 result is ambiguous at 1D. Then escalate to 2D.

## Q2. Particle count for toy worlds

**Question.** NPA is a particle system; should toy worlds have N > 1?

**Default.** N = 1 for G1/G2. The perception operators (SPH) still run but on a
single particle. Element conditioning and multi-species are irrelevant at N = 1
and are deferred to phase 3 (real chemistry). This keeps G2 focused on the state
question, not on SPH scaling.

## Q3. Training budget fairness for G2

**Question.** How much hyperparameter search does each variant get?

**Default.** Fixed budget: 3 learning rates × 2 hidden sizes = 6 configs per
variant, 5,000 steps each, same data, same seed. Total: 12 runs, ~minutes on
laptop. Report best-of-6 for each. This is small but honest; scaling up is a
phase-3 decision.

## Q4. "State helps" threshold

**Question.** What improvement counts as state helping?

**Default.** V3b must beat V2 by ≥ 10% relative on **both** barrier error and
rollout drift (measured on the held-out world) to count as a win. Smaller
differences are noise at this budget. A tie or V2 win is a negative result.

## Q5. V1 architecture fidelity

**Question.** Should V1 be the exact NPA architecture (shared trunk + element
conditioning) or a simpler MLP?

**Default.** Simpler MLP for toy worlds. The full NPA architecture (11k params,
SPH perception, element conditioning) is for phase 3 with real atoms. At N = 1
in 1D, element conditioning is meaningless. The V1 here is "NPA's update rule
shape" (direct dx, ds prediction), not "NPA's exact network."

## Q6. Langevin thermostat for non-conservative dynamics

**Question.** G2 needs non-conservative dynamics (friction + noise) for state to
matter. What friction coefficient and temperature?

**Default.** γ = 0.5, kT = 0.1, in reduced units. Barrier height ≈ 1.0 (so
kT/barrier ≈ 0.1, rare-event regime). These are standard; tune if trajectories
are trivially over/under-damped.

## Q7. Held-out world parameters

**Question.** How different should the held-out world be?

**Default.** Training world: barrier height 1.0, coupling 0.5. Held-out: barrier
height 1.3, coupling 0.7. Different enough to test generalisation, similar
enough that the same physics applies.

## Q8. Success metric for G1

**Question.** What does "the loop closes" mean concretely?

**Default.** V1 trained on the harmonic oracle recovers the force field to
force-MAE < 0.01 (in reduced units) on a held-out trajectory, and the rollout
drift over 1000 steps is < 1% of the oscillation amplitude. If V1 can't learn a
harmonic oscillator, nothing downstream will work.