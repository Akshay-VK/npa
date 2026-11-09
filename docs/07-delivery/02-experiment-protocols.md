---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-evaluation-design.md, 07-delivery/01-roadmap-and-kill-criteria.md]
---

# Experiment protocols

Concrete, runnable protocols for phases 1–4. Each protocol specifies the
data, the model, the evaluation, and the gate decision. No experiment runs
without a protocol.

**Bottom line**

- Phase 1 uses a synthetic Lennard-Jones + Gaussian barrier potential where
  the exact answer is known. No DFT.
- Phase 2 (the decision experiment) uses the same potential but four arms
  (endpoint vs force loss, with/without state). This is the phase that can
  kill the project.
- Phase 3 uses H + H₂ on a high-level reference surface. Small system.
- Phase 4 uses Transition1x subsets and a metadynamics free-energy profile.

## Phase 1 — Synthetic potential toolchain

**Data.** 2D two-species particle system, 50–100 particles, analytic potential
(Lennard-Jones repulsive core + attractive well + a single Gaussian barrier
$\Delta E = 5$ kcal/mol at $r = 2.5$ Å). Exact ground-state energies, barrier
height, and dissociation limits are analytic.

**Model.** Three variants, same architecture, different losses:
- **M1:** Direct position update, endpoint loss only.
- **M2:** Energy + autodiff forces, no latent state.
- **M3:** Energy + autodiff forces + persistent latent state.

**Protocol.**
1. Generate 10,000 training configurations and 2,000 test configurations.
2. Train each model for 500 epochs, Adam optimizer, $\lambda = 10^{-4}$ weight decay.
3. Seed each run 5 times (different weight initialisation).
4. Evaluate on test set: MAE on energy, barrier height (if applicable), and
   rollout energy drift over 10⁴ steps.
5. Run the stability battery (NVE drift, momentum conservation, time reversibility).

**Gate decision.** G1 pass: M2 conserves energy to <0.1% over 10⁴ steps in NVE.
If M2 fails, the integrator or force computation is wrong — stop and fix before
proceeding. If M2 passes but M3 does not improve on any metric, the state
contribution is not measurable at this scale — document as a null result and
proceed to phase 2 (the architecture decision).

**Artifact.** `v0.1-toolchain`.

## Phase 2 — The decision experiment

**Data.** Same synthetic potential as phase 1. Four arms, same data, same
parameter budget, same compute budget.

| Arm | Loss | State | Description |
|---|---|---|---|
| **A** | Endpoint only | yes | NPA-style baseline |
| **B** | Endpoint only | no | State contribution isolated |
| **C** | Per-step energy + force | yes | Proposed hybrid design |
| **D** | Per-step energy + force | no | Strong local baseline |

**Protocol.**
1. Train all four arms from the same random seed split, same hyperparameters,
   same number of gradient steps.
2. Measure: barrier-crossing rate, time-to-first-crossing, energy drift, rollout
   position error at horizons 1, 10, 100, 1000, regeneration test.
3. Use 5 seeds per arm.

**Gate decision.** G2 pass: C beats D on rollout error and barrier-crossing rate
at equal parameter count, with non-overlapping confidence intervals across 5 seeds.
If C ≈ D on both metrics, persistent state has no measurable benefit in the
simplest possible setting. Stop and write up as a negative result — this is a
publishable transferability result, not a project failure.

**Kill criterion.** If after a genuine tuning effort (equal hyperparameter search
budget, reported in GPU-hours), C ≈ D, the architecture is unsuitable for
dynamics. Stop and pivot to phase 5 Route B (energy surrogate scored on
observables).

**Artifact.** `v0.2-h3`.

> **In plain words.** Four versions of the same model, one difference each.
> If memory does not help even here, it will not help anywhere. This is the
> cheapest possible place to be wrong.

## Phase 3 — One real reaction

**Data.** H + H₂ → H₂ + H. Three-electron system. Exact barrier available from
literature (~9.5 kcal/mol). Generate a small reference set: 50 geometries spanning
reactant, saddle, and product, with CCSD(T)/CBS reference energies (or the
best available, with the level of theory explicitly stated).

**Model.** Train M2 and M3 on ωB97x/6-31G(d) single-point labels (from
Transition1x or a small AIMD set). Evaluate on the CCSD(T) reference set.

**Protocol.**
1. Train for 300 epochs, Adam, $\lambda = 10^{-4}$.
2. Seed 5 different initialisations.
3. Evaluate: barrier MAE vs CCSD(T), rotational invariance (rotate by random
   quaternion, compare energy), dissociation limit (separate H + H₂ to 20 Å).
4. Run one metadynamics free-energy profile using the learned potential and
   compare to DFT reference.

**Gate decision.** G3 pass: Barrier MAE < 1.5 kcal/mol; rotational invariance
to <1e-4 eV; correct dissociation limit.

**Kill criterion.** If the model cannot locate the barrier, or fails rotational
invariance after an honest equivariant attempt, the architecture is not
appropriate for real chemistry. Stop or pivot to phase 4 with a smaller
model/organic subset.

**Artifact.** `v0.3-h3`.

## Phase 4 — Organic reaction chemistry

**Data.** Transition1x subset: H/C/N/O, ≤7 heavy atoms. Train on 80% of
reactions, hold out 20% by reaction family (not random split).

**Model.** Train M3 (energy + force + latent state). Baselines: UMA fine-tuned,
MACE trained from scratch, PBE, ωB97M-V.

**Protocol.**
1. Train for 500 epochs, Adam, $\lambda = 10^{-4}$.
2. Seed 5 different initialisations.
3. Evaluate on held-out family: barrier MAE, reaction energy MAE, rollout
   stability (10⁴ steps NVE), cost per trajectory.
4. Run one metadynamics free-energy profile on a single reaction and compare
   to DFT.

**Gate decision.** G4 pass: Competitive barrier MAE with the fine-tuned UMA
baseline at ≥10× lower inference cost, or better barrier MAE at equal cost.

**Kill criterion.** Worse on both accuracy and cost with no compensating
advantage. Document and stop, or pivot to phase 5 Route B (benchmark contribution).

**Artifact.** `v1.0-transition1x`.

## Protocol common requirements

Every protocol must specify:

1. **Random seed** control and logging.
2. **Hardware** and software stack (including versions).
3. **Data manifest** with checksums.
4. **Metric template** filled (see [metrics and statistics](../05-evaluation/02-metrics-and-statistics.md)).
5. **Gate reference** (G0–G4) and the decision rule.

> **In plain words.** No experiment runs without a plan. The plan says what
> data, what model, what evaluation, and what decision. If any of those is
> missing, the experiment is not ready.

## What would change this document

- A published evaluation protocol from the challenge organisers, which would
  standardise the protocol format across projects.
- Evidence that a different protocol (e.g. random test-split instead of
  family-held-out) changes the results substantially.
- A decision to skip a phase, which would compress the roadmap.

## Open questions

- Should phase 3 use a CCSD(T) reference, or is ωB97x/def2-TZVP sufficient?
  This determines the cost of phase 3.
- How many Transition1x reactions should be in the hold-out set? 20% is the
  default, but with only 10k reactions, this gives 2k hold-out. Is that enough
  for a reliable family-level split?
- Should metadynamics be run in phase 3 (H + H₂) or deferred to phase 4? H +
  H₂ is the one case where accurate quantum dynamics exist; including it gives
  a direct DFT comparison.

## What would change this document

- A published evaluation protocol from the challenge organisers, which would
  standardise the protocol format across projects.
- Evidence that a different protocol changes the results substantially.
- A decision to skip a phase, which would compress the roadmap.

## Sources

1. Schreiner et al., *Transition1x*, Scientific Data 9, 2022.
   <https://www.nature.com/articles/s41597-022-01870-w> (retrieved 2026-11-07).
2. Kim et al., *Neural Particle Automata*, arXiv:2601.16096.
   <https://arxiv.org/abs/2601.16096> (retrieved 2026-11-07).
3. Eyring, *The activated complex in chemical reactions*, J. Chem. Phys. 3,
   107 (1935). <https://doi.org/10.1063/1.1749604> (retrieved 2026-11-07).
4. Laio and Parrinello, *Escaping free-energy minima*, PNAS 99, 12562 (2002).
   <https://doi.org/10.1073/pnas.202427399> (retrieved 2026-11-07).
5. Bussi, Donadio and Parrinello, *Canonical sampling through velocity
   rescaling*, J. Chem. Phys. 126, 014101 (2007).
   <https://doi.org/10.1063/1.2408420> (retrieved 2026-11-07).