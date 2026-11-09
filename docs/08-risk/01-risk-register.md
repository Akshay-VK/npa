---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [../00-orientation/03-critical-assessment-of-the-idea-note.md]
---

# Risk register

Every risk that could invalidate the project, scored, with a mitigation and an
early-warning signal. The source note lists seven; this register keeps all
seven (two with corrected reasoning), adds eighteen more that it misses, and
attaches a kill criterion to the ones that can end the project.

**Bottom line**

- The project's three existential risks are **R-01 (attractor training
  suppresses reactions)**, **R-09 (latent state breaks conservation)**, and
  **R-26 (the small-model premise is false)**. Everything else is recoverable.
- The source note's risk table is directionally right but misses the two
  failure modes that come from NPA itself, rather than from chemistry.
- Six risks are **cheap to test now** and expensive to discover later. Those
  are the first experiments.
- Two risks (R-07 metals, R-17 deployment) are scope risks disguised as
  technical ones. They should be resolved by a decision, not an experiment.

## Scoring convention

| | **Impact low** | **Impact medium** | **Impact high** |
|---|---|---|---|
| **Likelihood high** | track | mitigate | **existential** |
| **Likelihood medium** | accept | mitigate | mitigate |
| **Likelihood low** | accept | track | plan |

"Existential" means the project as framed cannot continue; it must be
re-scoped, not fixed.

> **In plain words.** Some risks are annoying, some are expensive, and three
> can end the project. This table sorts them so effort goes to the ones that
> matter, not the ones that are easiest to talk about.

## The register

| ID | Risk | L | I | Score | First test |
|---|---|---|---|---|---|
| R-01 | Attractor/endpoint training suppresses barrier crossing | H | H | **Existential** | Phase 2, arm C |
| R-02 | Rollout error compounds over long horizons | H | H | **Existential** | Phase 1 rollout |
| R-03 | No reactive events in the training distribution | H | H | **Existential** | Data audit |
| R-04 | Hidden state injects or leaks energy | H | H | **Existential** | Phase 1 energy audit |
| R-05 | Hidden state is unidentifiable / used as a scratchpad | H | M | Mitigate | State ablation |
| R-06 | Short-range locality misses electrostatics and dispersion | H | M | Mitigate | Long-range test |
| R-07 | Scope excludes transition metals the benchmark needs | H | H | **Existential (scope)** | Decision |
| R-08 | No rotational equivariance | H | H | **Existential** | Rotation test |
| R-09 | Accuracy ceiling set by labels | H | M | Mitigate | Multi-fidelity plan |
| R-10 | Compute and data cost exceed budget | M | H | Mitigate | Budget review |
| R-11 | Crowded field / scoop | M | M | Track | Literature watch |
| R-12 | Detached moment matrix destabilises force training | M | H | Mitigate | Phase 1 |
| R-13 | Fixed particle count, no merge/split | M | M | Accept + document | Phase 2 |
| R-14 | Spin and charge states not represented | H | H | Mitigate | Phase 3 |
| R-15 | Benchmark leakage inflates results | M | H | Mitigate | Split audit |
| R-16 | Statistical underpower (too few seeds) | H | M | Mitigate | Power analysis |
| R-17 | No path to deployment / integration | M | H | Mitigate | Decision |
| R-18 | Team lacks quantum chemistry judgement | M | H | Mitigate | Advisor |
| R-19 | Scope creep into functional territory | M | M | Mitigate | ADR review |
| R-20 | Data licensing blocks use or publication | L | H | Plan | Licence audit |
| R-21 | GPU non-determinism breaks reproducibility | H | M | Mitigate | Seed test |
| R-22 | Hardware budget insufficient for phase 4 | M | H | Plan | Costing |
| R-23 | Negative result unpublishable | M | M | Mitigate | Pre-registration |
| R-24 | "Small model" premise false — scale is required | H | H | **Existential** | Scaling curve |
| R-25 | Evaluation mismatch (optimising the wrong metric) | H | M | Mitigate | Metric review |

## Existential risks, in detail

### R-01 — Attractor training suppresses reactions

**Why it matters.** NPA's headline properties — regeneration, robustness,
convergence to a target — are produced by training on a *final state*, not a
path. A model optimised to return to an attractor will damp the fluctuation
that should become a reaction. This is the deepest conceptual mismatch between
the graphics problem and the chemistry problem, and it is invisible in
single-point metrics. Full argument in
[the critical assessment](../00-orientation/03-critical-assessment-of-the-idea-note.md).

**Likelihood.** High if the architecture is ported naively. Medium if the loss
is force-based from the start.

**Impact.** High. If the only thing NPA contributes is attractor behaviour, it
contributes nothing to chemistry.

**Mitigation.**
1. Train with per-frame energy and force supervision, never endpoint-only.
2. Run the explicit A/B: same architecture, endpoint loss vs force loss, same
   data. Measure barrier-crossing rate in rollout.
3. Evaluate on barrier height, not just trajectory similarity.
4. Treat regeneration as a **failure** in chemistry, not a feature. Add a
   "does it resist reaction?" test.

**Early warning.** Rollouts started on the product side drift back to the
reactant. Barrier height is systematically underestimated. Perturbation is
repaired rather than propagated.

**Kill criterion.** If the force-trained model still cannot cross a known
barrier in the toy world, the architecture is unsuitable for dynamics.

> **In plain words.** A model trained to heal itself will heal a bond that is
> trying to break. Test this in week two, not month six.

### R-02 — Rollout error compounds

**Why it matters.** A 1% force error at each step is a 1% error in the
trajectory, but small phase errors accumulate and can change *which basin* the
system ends in. One-step accuracy does not imply long-horizon accuracy.

**Likelihood.** High for any learned dynamics model.

**Impact.** High, unless the model is energy-based with a stable integrator, in
which case errors stay bounded by the energy surface.

**Mitigation.**
1. Prefer energy-based dynamics (Variant 2/3) over direct updates.
2. Train with multi-step rollouts, not single steps (curriculum: 1 → 4 → 16
   steps).
3. Use a symplectic or Langevin integrator with a real timestep.
4. Report drift curves at 10², 10³, 10⁴ steps, not one number.
5. Add a "stability envelope": the temperature and timestep range in which the
   model does not blow up.

**Early warning.** Energy drifts monotonically. RMSD grows as $\sqrt{t}$
instead of plateauing. Temperature creeps despite a thermostat.

**Kill criterion.** If energy drift exceeds 1% over 10⁴ steps at 300 K after
multi-step training, the model cannot be used for long trajectories.

> **In plain words.** Small mistakes in a movie add up until the plot changes.
> The fix is to make the model follow a landscape, so it cannot wander off it.

### R-03 — No reactive events in the data

**Why it matters.** At 300 K, a reaction with a 25 kcal/mol barrier has a rate
of roughly $10^{-5}\ \mathrm{s^{-1}}$ — one event per day per molecule, against
a vibrational attempt frequency of $\sim 10^{13}\ \mathrm{s^{-1}}$. Ordinary MD
contains no reactions. Training on it teaches the model that bonds never
break.

**Likelihood.** High if data comes from equilibrium MD or standard datasets.

**Impact.** High, and it is silent: the model looks excellent on the test set
because the test set is also non-reactive.

**Mitigation.**
1. Use Transition1x-style path data for the saddle region.
2. Generate targeted reactive trajectories: high temperature, constrained
   sampling, metadynamics, or scripted bond stretching.
3. Include dissociation limits explicitly.
4. Stratify the test set by distance from equilibrium and report per-stratum
   error.
5. Never report a single aggregate error over a dataset that is 99% equilibrium.

**Early warning.** Excellent validation loss, terrible barrier heights. Model
predicts smooth, monotonic behaviour where a saddle should be.

**Kill criterion.** If no reactive data can be obtained at the target chemistry,
the project is limited to a non-reactive potential and should say so.

> **In plain words.** If every photo in the album shows people standing still,
> the model will never learn to predict dancing.

### R-04 — Hidden state injects or leaks energy

**Why it matters.** If the energy is $E(\mathbf{x}, \mathbf{s})$ and the latent
state $\mathbf{s}$ evolves by a learned rule, then the total derivative along a
trajectory is

$$
\frac{dE}{dt} = \sum_i \frac{\partial E}{\partial \mathbf{x}_i}\cdot\dot{\mathbf{x}}_i
+ \sum_i \frac{\partial E}{\partial \mathbf{s}_i}\cdot\dot{\mathbf{s}}_i .
$$

The first term is the mechanical power and is handled by the integrator. The
second term is an **unaccounted energy source or sink**. A model can therefore
appear conservative in its force law and still heat or cool the system through
its state update. This is the single most under-appreciated technical risk in
the hybrid design, and the prior run of this project caught it independently.

**Likelihood.** High. Any learned state dynamics will do this unless explicitly
constrained.

**Impact.** High. It invalidates energy-drift results, can create spurious
reactions, and makes temperature meaningless.

**Mitigation.**
1. **Constrain the state update to be non-expansive in energy:** either
   (a) treat state as a *relaxed auxiliary variable* solved to a minimum at
   each step (so it carries no independent dynamics), or
   (b) add an explicit energy accounting term and verify
   $\Delta E_{\text{mech}} + \Delta E_{\text{state}} = 0$ to tolerance.
2. Make state **slow** relative to positions, so its contribution is small.
3. Add a regulariser penalising $\partial E/\partial \mathbf{s}\cdot\dot{\mathbf{s}}$.
4. Log the state-energy term in every rollout; do not hide it.
5. Consider a "conservative latent" formulation where state is a function of
   the trajectory history, not an independent dynamical variable.

**Early warning.** Energy drift correlates with state magnitude. Turning off
the state update reduces drift. Temperature rises in NVE when state is active.

**Kill criterion.** If the state-energy term cannot be bounded below ~1% of the
mechanical energy change over a trajectory, the hybrid is not conservative
enough to call a potential.

> **In plain words.** If the model's memory can change the energy, it is a
> hidden battery. It will charge and discharge and you will not notice until
> your simulation is at the wrong temperature.

### R-07 — Scope excludes transition metals

**Why it matters.** The challenge's hidden benchmark is ALD/CVD precursor
chemistry. Precursors include trimethylaluminium, TiCl₄, TEMAH (Hf), copper
amidinates, and similar. These are metals. The project's initial scope is
H/C/N/O. That is not a small gap; it is the difference between the demo
chemistry and the target chemistry.

**Likelihood.** Certain, given the stated scope.

**Impact.** High for challenge fit; medium for the research claim.

**Mitigation.**
1. Decide explicitly: is the goal a challenge submission (needs metals) or a
   research result (does not)? This is [ADR 0002](../adr/0002-research-first-not-submission.md).
2. If metals are needed, budget for a separate data and validation effort.
   Transition-metal MLIPs are materially harder: multiple spin states,
   near-degeneracies, strong correlation.
3. Do not claim ALD relevance until at least one metal-containing system has
   been tested.

**Early warning.** A reviewer asks "does it work on TMA?" and there is no
answer.

> **In plain words.** The competition's chemistry contains aluminium and
> titanium. Ours currently contains hydrogen, carbon, nitrogen and oxygen.
> Pretending those are the same is the easiest way to waste a year.

### R-08 — No rotational equivariance

**Why it matters.** Rotating a molecule must not change its energy. NPA
explicitly does not enforce rotational equivariance; the paper says the
gradient perceptions "assume global Euclidean basis, limiting the model's
generalization over rotations."

**Likelihood.** Certain, if the architecture is ported as published.

**Impact.** High. It is a correctness bug, not a performance issue.

**Mitigation.**
1. Use invariant scalar inputs (distances, angles) plus equivariant vector
   outputs, or an equivariant backbone (e3nn, MACE-style).
2. If starting from NPA's SPH features, replace the Euclidean gradient features
   with rotation-invariant combinations (e.g. $|\nabla\mathbf{S}|$,
   $\nabla\mathbf{S}:\nabla\mathbf{S}^\top$).
3. Test: rotate a configuration by a random quaternion, compare energy and
   force magnitude. Tolerance should be numerical, not "close".
4. Augmentation is a stopgap, not a fix: it does not guarantee equivariance at
   inference.

**Early warning.** Energy varies by more than 1e-4 eV under rotation. Force
vectors rotate incorrectly.

> **In plain words.** Turn the molecule around and the answer must not change.
> If it does, the model is not learning physics, it is learning a coordinate
> system.

### R-24 — The small-model premise is false

**Why it matters.** The project's most attractive claim is that a 10k-parameter
rule can carry real chemistry. The NPA paper's 11k-parameter results are for
2D morphogenesis, where the target is a picture. Chemistry may require orders
of magnitude more capacity.

**Likelihood.** High. Accuracy in MLIPs correlates with parameters and data.

**Impact.** High. If true, the project's distinctive cost advantage disappears
and it becomes a worse UMA.

**Mitigation.**
1. Measure the scaling curve early: parameter count vs barrier MAE, at fixed
   data. If the curve is steep, the premise is dead and you learn it cheaply.
2. Separate *capacity* from *inductive bias*. A small model with the right
   physics can beat a large one with the wrong physics on a narrow task; test
   both axes.
3. Define the cost advantage precisely: parameters, FLOPs per step, or
   wall-clock per trajectory. They are different claims.

**Early warning.** Barrier error plateaus at a high value regardless of
training time. Adding parameters helps linearly with no sign of saturation.

**Kill criterion.** If a 10× parameter increase gives a >2× barrier-error
reduction with no plateau, the "tiny model" story is over.

> **In plain words.** Maybe chemistry needs a big brain, not a small one.
> Measure that before writing the paper about small brains.

## Serious-but-recoverable risks

### R-05 — Hidden state is unidentifiable

The model may use latent channels as a scratchpad encoding arbitrary
information (position history, dataset identity, noise) rather than anything
physical. This is not necessarily fatal — it may still improve accuracy — but
it destroys interpretability and transfer.

*Mitigation:* ablate state at inference and measure the drop. Probe state
channels with linear regression against physical quantities (charge, spin,
coordination). Require that state can be re-initialised from a physical guess
without catastrophic loss. If the model cannot run with state zeroed, it is
using state as memory of the wrong kind.

> **In plain words.** The model might be using its memory to remember where it
> has been, not what the electrons are doing. That still helps, but it is not
> what we claimed.

### R-06 — Short-range locality

Cutoffs truncate electrostatics and dispersion. *Mitigation:* explicit
long-range term (Ewald, learned charges, D3/D4), or a two-range architecture.
Test with separated fragments at 10, 20, 50 Å.

### R-09 — Label ceiling

Training on ωB97M-V data caps accuracy at ωB97M-V. *Mitigation:* multi-fidelity
(cheap labels for coverage, expensive labels for correction), Δ-learning
against a physical baseline, and a small CCSD(T) holdout. See
[label fidelity](../04-data/03-label-fidelity-and-multifidelity.md).

### R-12 — Detached moment matrix under force training

NPA's stabilisation trick detaches the first-order gradient correction. Image
losses tolerate this; force losses are far more sensitive to geometry.
*Mitigation:* test with the correction attached and detached; monitor force
smoothness; fall back to 0th-order if unstable.

### R-14 — Spin and charge

Reactions change electronic state. A single implicit state cannot represent
singlet–triplet crossings. *Mitigation:* condition on total charge and
multiplicity; test on a known open-shell reaction; consider separate models per
spin state as a baseline.

### R-15 — Benchmark leakage

GMTKN55 and Transition1x appear in pretraining corpora. *Mitigation:*
graph-level overlap removal (as Skala does), not random splits. Report the
overlap analysis.

### R-16 — Statistical underpower

Three seeds and a mean are not evidence. *Mitigation:* pre-register the effect
size, compute seeds needed, report confidence intervals, use paired tests on
the same test set.

### R-17 — Deployment

Even a good model needs an interface. *Mitigation:* expose an ASE calculator
early; that makes it usable by everyone and forces the units and determinism
questions to be answered.

### R-18 — Skills gap

Quantum chemistry judgement is not optional. *Mitigation:* one advisor or
collaborator who can veto a chemically absurd result; otherwise the project
will publish something embarrassing.

### R-19 — Scope creep into functional territory

The grid-particle extension is seductive and expensive. *Mitigation:* ADR gate;
no work on it before phase 5.

### R-20 — Licensing

OMol25, Transition1x, UMA, and MACE have different licences. *Mitigation:*
audit before training; record licence and version in the data manifest.

### R-21 — GPU non-determinism

cuBLAS and atomics make bitwise reproducibility hard. *Mitigation:* fix seeds,
disable TF32 where it matters, report run-to-run variance, publish configs and
container.

### R-22 — Hardware

Phase 4 needs GPU-hours. *Mitigation:* cost it before promising it; prefer
small models and cached features.

### R-23 — Negative results are hard to publish

*Mitigation:* pre-register the phase-2 experiment and frame it as a
transferability study, which is publishable regardless of outcome.

### R-25 — Evaluation mismatch

Optimising force MAE while claiming rate accuracy. *Mitigation:* fix the
observable hierarchy in [evaluation design](../05-evaluation/01-evaluation-design.md)
before training.

## The matrix

```
Impact
 high |  R-10 R-17 R-18   R-02 R-03 R-04   R-01 R-07 R-08
      |  R-22 R-15        R-14 R-24
 med  |  R-11 R-19 R-23   R-05 R-06 R-09   R-16
      |                   R-12 R-13 R-25
 low  |                   R-20 R-21
      +------------------------------------------------
         low              medium            high      Likelihood
```

*(inference)* The cluster in the top-right is where the first month's effort
should go. Five of those six can be tested in the toy world for almost no
money.

> **In plain words.** The dangerous risks are not the exotic ones. They are the
> obvious ones that are cheap to test and embarrassing to discover late.

## Risks the source note handles well

Worth saying explicitly, because the note is good at this:

- **Compounding rollout error** — correctly identified, correctly mitigated by
  preferring energy-based variants.
- **Rare reactive events** — correctly identified as the central data problem.
- **Label ceiling** — correctly identified, including the multi-fidelity fix.
- **Crowded field** — correctly identified, though "tiny and fast models" is
  not as empty a niche as the note implies; ANI and SchNet occupy part of it.
  The genuine niche is *persistent state plus conservative energy*.

## Risks the source note mis-scopes

- **Per-element networks** are presented as a force-consistency problem. They
  are a pair-symmetry and data-cost problem. Force consistency is solved by a
  shared energy sum.
- **Rotation equivariance** is presented as "unclear". The NPA paper states it
  is not enforced. It is a known defect, not an open question.
- **"Multi-species"** is presented as an existing mechanism to study. It is
  independent-model composition, not a species mechanism.

## Review cadence

Re-score this register at each phase gate. A risk that has not changed status
in two phases is either retired or not being tested. Record the change in
`docs/09-sources/02-verification-log.md` if a numeric claim moves.

## Open questions

- Which risks are genuinely independent? R-01, R-02 and R-04 may all reduce to
  "the model is not a conservative dynamical system", in which case one fix
  addresses three rows.
- Is R-24 testable without a full training run, e.g. by a linear probe on
  features?
- Does R-07 (metals) have a cheap proxy, such as a single Al-containing
  reaction?

## What would change this document

- Phase 1 results, which will re-score R-01, R-02, R-04, R-12 and R-24.
- A published particle-automaton potential, which would retire R-01 and R-08
  by demonstrating they are solvable.
- A decision to pursue the challenge seriously, which would promote R-07 from
  scope risk to project risk.

## Sources

Risks R-01, R-05, R-08, R-09, R-12 and R-24 derive from the NPA paper's own
limitations and methods sections (arXiv:2601.16096); R-02, R-03, R-06, R-09 and
R-11 from the source note and the Transition1x paper (arXiv:2207.12858); R-07
and R-14 from the challenge page and the ALD chemistry literature; R-09 and
R-10 from Skala (arXiv:2506.14665) and OMol25 (arXiv:2505.08762). See the
[annotated bibliography](../09-sources/01-annotated-bibliography.md) for full
citations.
