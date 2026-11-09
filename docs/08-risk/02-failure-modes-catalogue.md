---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-risk-register.md]
---

# Failure modes catalogue

Physics and machine-learning failure modes, with symptoms and diagnostics. This
catalogue describes what can go wrong in an atomistic dynamics surrogate, how
to recognise the symptoms, and what to check diagnostically. It is distinct
from the risk register (which scores risks by likelihood and impact) because it
focuses on the mechanism of the failure, not just its severity.

**Bottom line**

- Seven failure modes are listed, each with a symptom, a diagnostic test, and a
  mitigation.
- Three of them (F-M01, F-M04, F-M07) are the most dangerous because they
  are silent — the model looks accurate on standard benchmarks while being
  wrong in the regime that matters.
- Two modes (F-M02, F-M05) are detectable with the stability battery from
  [rollout stability and physics tests](../05-evaluation/03-rollout-stability-and-physics-tests.md).
- Two modes (F-M03, F-M06) are detectable with the observable hierarchy from
  [evaluation design](../05-evaluation/01-evaluation-design.md).

## F-M01 — Barrier suppression by attractor training

**Mechanism.** The model is trained on endpoint energies (or a rendered final
state) rather than per-frame forces. The loss rewards convergence to a stable
attractor (the product basin), which dampens the very fluctuation that should
become a reaction. This is the deepest conceptual mismatch between the graphics
problem (target-state learning) and the chemistry problem (barrier crossing).

**Symptoms.**
1. Excellent validation MAE on equilibrium geometries.
2. Barrier heights systematically underestimated (or completely absent).
3. Perturbed trajectories return to the reactant basin instead of crossing.
4. Energy drift that correlates with the distance from the reactant geometry.

**Diagnostic test.**
1. Train the same architecture with a per-frame force-loss alongside the
   endpoint loss. Compare barrier heights.
2. Run the regeneration test: start a trajectory on the product side and
   see whether the model resists returning. If it does — it is suppressing
   reactions.
3. Check the barrier MAE on a held-out test set that includes stretched
   configurations near the saddle.

**Mitigation.** Train with force supervision from the start. If using an
endpoint loss, always supplement with a per-step energy or force term. See
[R-01](../08-risk/01-risk-register.md) in the risk register.

> **In plain words.** The model is trained to end up in the right shape, and it
> is proud that it repairs itself if you break it. A chemical reaction is the
> opposite: the molecule has to stop repairing itself and fall apart in a
> specific way. A self-healing model is a model that refuses to react.

## F-M02 — Rollout energy drift

**Mechanism.** The model's energy is not conserved along trajectories. For an
energy-based model, this means the persistent state injects or leaks energy
(see F-M04). For a direct-update model, it means the integrator is not
symplectic or the model's forces are not the gradient of a potential.

**Symptoms.**
1. Monotonic energy drift over a trajectory (NVE ensemble).
2. Temperature creep despite a thermostat.
3. Momentum non-conservation (total momentum changes).
4. The model produces smooth trajectories that gradually accelerate or decelerate.

**Diagnostic test.**
1. Run the NVE energy conservation test from the stability battery:
   drift < 0.1% over 10⁴ steps.
2. Compare energy drift with the state update on vs. off.
3. Check momentum conservation: total momentum should be constant to machine
   precision in NVE.

**Mitigation.**
1. Energy-based models must constrain the state update to be non-expansive in
   energy (see [R-04](../08-risk/01-risk-register.md)).
2. Direct-update models must use a symplectic integrator (velocity Verlet).
3. Report energy drift in every result table.

> **In plain words.** If the model's memory can change the energy, it is a
> hidden battery. It will charge and discharge and you will not notice until
> your simulation is at the wrong temperature.

## F-M03 — Short-range locality misses long-range physics

**Mechanism.** The model has a cutoff radius beyond which interactions are
zero. Electrostatics ($1/r$) and dispersion ($1/r^6$) decay slowly and are
wrongly truncated. The model learns to compensate within the cutoff, which
works for equilibrium geometries but fails for separated fragments or
transition states where fragments are far apart.

**Symptoms.**
1. Excellent MAE on GMTKN55 or OMol25 (which lack separated-fragment test
   sets).
2. Large error on configurations where fragments are beyond the cutoff.
3. Correct binding energies for small molecules, wrong ones for large ones.
4. Dissociation limit does not approach the sum of fragment energies.

**Diagnostic test.**
1. Separate fragments to 10, 20, 50 Å and compare the model's energy to the
   sum of fragment energies.
2. Test on the dimerisation energy of TMA (Al₂(CH₃)₆) or another metal-
   containing system.
3. Compare the model's error on equilibrium vs. stretched configurations.

**Mitigation.**
1. Add an explicit long-range term: Ewald summation, learned charges, or D3/D4
   dispersion correction.
2. Use a two-range architecture: short-range NN + analytical long-range.
3. Train on configurations that include separated fragments.

> **In plain words.** The model is brilliant at what it has seen, but it has
> never seen a molecule stretch to infinity. It will confidently give the wrong
> answer for separated fragments unless you force it to learn the long-range
> physics.

## F-M04 — Hidden state injects or leaks energy

**Mechanism.** The total energy is $E(\mathbf{x}, \mathbf{s})$ and the latent
state $\mathbf{s}$ evolves by a learned rule. The total derivative along a
trajectory is

$$
\frac{dE}{dt} = \sum_i \frac{\partial E}{\partial \mathbf{x}_i}\cdot\dot{\mathbf{x}}_i
+ \sum_i \frac{\partial E}{\partial \mathbf{s}_i}\cdot\dot{\mathbf{s}}_i .
$$

The second term is an unaccounted energy source or sink. The model can appear
conservative in its force law and still heat or cool the system through its
state update.

**Symptoms.**
1. Energy drift that correlates with state magnitude.
2. Turning off the state update reduces drift.
3. Temperature rises in NVE when the state is active.
4. The model's energy is not conserved along trajectories even when the
   forces are the gradient of the energy.

**Diagnostic test.**
1. Run the energy drift test with the state update on vs. off.
2. Compute the state-energy term $\sum_i \frac{\partial E}{\partial \mathbf{s}_i}\cdot\dot{\mathbf{s}}_i$
   along a trajectory and check whether it is bounded.
3. Verify that $\Delta E_{\text{mech}} + \Delta E_{\text{state}} = 0$ to tolerance.

**Mitigation.**
1. Constrain the state update to be non-expansive in energy: either (a) treat
   state as a relaxed auxiliary variable solved to a minimum at each step, or
   (b) add an explicit energy accounting term and verify the balance.
2. Make state slow relative to positions, so its contribution is small.
3. Add a regulariser penalising $\partial E/\partial \mathbf{s} \cdot \dot{\mathbf{s}}$.
4. Log the state-energy term in every rollout; do not hide it.

> **In plain words.** If the model's memory can change the energy, it is a
> hidden battery. It will charge and discharge and you will not notice until
> your simulation is at the wrong temperature.

## F-M05 — Unidentifiable hidden state

**Mechanism.** The model uses latent channels as a scratchpad encoding arbitrary
information (position history, dataset identity, noise) rather than anything
physical. This is not necessarily fatal — it may still improve accuracy — but
it destroys interpretability and transfer to new systems.

**Symptoms.**
1. Ablating a state channel has little effect on accuracy.
2. State channels cannot be re-initialised from a physical guess without
   catastrophic loss.
3. Linear probing of state channels against physical quantities (charge, spin,
   coordination) yields poor regression results.
4. The model cannot run with state channels zeroed — it depends on them for
   something other than the intended physical role.

**Diagnostic test.**
1. Ablate each state channel at inference and measure the drop in accuracy.
2. Try re-initialising state from a physical guess (e.g. zero charge, zero
   spin) and see whether the model survives.
3. Run linear regression of each state channel against physical quantities
   (from a dataset of configurations with known charges/spins).

**Mitigation.**
1. If ablating a channel drops accuracy significantly, the channel is doing
   something useful — document what it appears to encode.
2. If re-initialising from a physical guess causes catastrophic loss, the
   state is using memory of the wrong kind — consider whether the architecture
   is appropriate.
3. If the model cannot run with state zeroed, document this as a limitation
   and consider an architecture where state is optional.

> **In plain words.** The model might be using its memory to remember where it
> has been, not what the electrons are doing. That still helps, but it is not
> what we claimed.

## F-M06 — Evaluation mismatch (optimising the wrong metric)

**Mechanism.** The model is evaluated on a metric that does not correspond to
the project's actual goal. Example: optimising force MAE while claiming rate
accuracy; optimising equilibrium MAE while the target is barrier heights;
optimising single-point energy while the target is rates.

**Symptoms.**
1. Excellent validation loss on the reported metric.
2. Poor performance on the actual goal (barriers, rates, dissociation).
3. Reviewer or reader asks "how does this translate to rates?" and the answer
   is unclear or unavailable.
4. The result is published as "accurate" but cannot answer the project's
   core question.

**Diagnostic test.**
1. Map the reported metric to the observable hierarchy (energy, barrier, rate).
2. Report all three tiers, even if the primary is only one.
3. Check that the baseline set values are included for comparison.

**Mitigation.**
1. Fix the observable hierarchy in [evaluation design](../05-evaluation/01-evaluation-design.md)
   before training.
2. Report all three tiers in every result table.
3. If the primary metric is not the one the project cares about, state this
   explicitly and say what the primary metric actually measures.

> **In plain words.** You cannot optimise force MAE and claim rate accuracy.
> The three tiers are energy, barrier, and rate. Pick the one you care about
> and report the others.

## F-M07 — Statistical underpower

**Mechanism.** The experiment runs too few seeds to distinguish real effects
from noise. A result that looks like a difference may be chance variation.

**Symptoms.**
1. A single seed shows a large improvement, and the mean is reported without
   interval.
2. The 95% confidence interval overlaps zero or with the baseline.
3. The effect size is not much larger than the standard deviation across seeds.
4. The paper says "the difference is not statistically significant" but still
   presents it as a result.

**Diagnostic test.**
1. Report the mean and standard deviation across all seeds.
2. Report a confidence interval or a seed-by-value table.
3. Perform a power analysis before the experiment and report the result against
   the design.

**Mitigation.**
1. Pre-register the effect size and the number of seeds needed.
2. Run ≥5 seeds as the default. Fewer than 3 should be explicitly flagged.
3. If fewer seeds were run, report the seed-by-value table and do not claim
   a significant difference.

> **In plain words.** Three seeds and a mean are not evidence. If you do not
> know the effect size you are looking for, you cannot design a properly
> seeded experiment. Say what you are looking for, and run enough seeds to
> see it.

## Mode severity summary

| Mode | Detectable by | Silent if | Mitigation cost |
|---|---|---|---|
| F-M01 | Observable hierarchy + regeneration test | Barrier suppression invisible in equilibrium MAE | Low (training loss change) |
| F-M02 | Stability battery (energy drift) | Drift invisible in single-point MAE | Medium (architecture change) |
| F-M03 | Stretched-fragment test | Wrong for separated fragments, fine for equilibrium | Medium (long-range term) |
| F-M04 | State-on vs. state-off energy drift | Drift invisible in single-point MAE | Medium (energy constraint) |
| F-M05 | Ablation + re-initialisation test | State appears necessary for accuracy | Low (document limitation) |
| F-M06 | Reporting all three tiers | Only one tier reported | Low (reporting change) |
| F-M07 | Power analysis + seed report | Few seeds, no interval reported | Low (planning change) |

> **In plain words.** The dangerous modes are not the ones that are hard to
> detect. They are the ones that are silent — they look like success on the
> metrics you are reporting, while failing on the thing you actually care about.
> F-M01, F-M04, and F-M07 are the most dangerous.

## Relation to the risk register

| Risk ID | Related failure mode(s) |
|---|---|
| R-01 | F-M01 |
| R-02 | F-M02 |
| R-03 | F-M03 |
| R-04 | F-M04 |
| R-05 | F-M05 |
| R-06 | F-M03 |
| R-08 | F-M01 |
| R-09 | F-M04 |
| R-12 | F-M04 |
| R-14 | F-M05 |
| R-16 | F-M07 |
| R-25 | F-M07 |

> **In plain words.** Seven failure modes map to fifteen risk rows. The most
> dangerous failures are those that are silent — they look like success on the
> metrics you report while failing on the thing you actually care about.

## What would change this document

- A published taxonomy of failure modes from the wider ML-for-chemistry community,
  which would allow cross-referencing and consolidation.
- A demonstration that one of the listed modes is actually impossible under
  certain architectural constraints, which would retire that mode.
- A new failure mode discovered during an experiment, which would be added as
  an appendix and the document updated.

## Sources

1. Roth et al., *The devil is in the detail: progressive network distortion in
   deep generative models*, ICLR (2020) — for the concept of hidden state as
   scratchpad.
2. Bardenet et al., *On the benchmark and evaluation of molecular dynamics
   potentials*, J. Chem. Phys. 155, 054105 (2021).
   <https://doi.org/10.1063/5.0008685> (retrieved 2026-11-07).
3. Smith et al., *Lessons learned in molecular dynamics modelling with machine
   learning potentials*, npj Computational Materials 7, 20 (2021).
   <https://doi.org/10.1038/s41524-020-00496-5> (retrieved 2026-11-07).
4. Lubbers and Verstraelen, *Machine learning molecular potentials: a critical
   review*, WIREs Computational Molecular Science (2021).
   <https://doi.org/10.1002/wcms.1473> (retrieved 2026-11-07).