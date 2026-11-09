---
status: draft
confidence: high
last_verified: 2026-11-09
depends_on: [01-roadmap-and-kill-criteria.md, 02-experiment-protocols.md, ../04-data/01-dataset-landscape.md]
---

# G2d and G3 plan: state where memory is necessary, and one real reaction

G2 showed that persistent latent state tracks hidden variables but does not improve
prediction on conservative systems. G2d closes that gap by testing a system where
memory is *necessary*: a multi-particle world with a hidden per-particle phase that
a stateless model cannot observe. G3 then asks whether any of the machinery survives
contact with real electronic structure. This document fixes the G2d design, lays out
three concrete G3 running options, and states the decision rule so the next stage
does not depend on hindsight.

This document is the **design record**. The G2d result is in
[`11-g2d-results.md`](11-g2d-results.md) and the G3 result is in
[`12-g3-results.md`](12-g3-results.md); where a plan expectation differs from the
measured outcome, the result documents govern.

**Bottom line**

- G2d uses a non-conservative multi-particle world with a hidden per-particle phase;
  V1 (direct), V2 (stateless energy) and V3b (latent energy) share the same perception.
- The fair G2d test is *same dynamics, new initial conditions*; a shifted-parameter
  run is reported separately as a robustness stress test, not as the gate.
- G3 Option 1 is the only one-day, zero-budget option that measures the actual G3
  quantity: a self-generated H + H₂ → H₂ + H barrier with PySCF.
- G3 Option 2 (Transition1x) validates the pipeline on a real organic reaction but
  cannot supply H₃; it is early G4, not G3.
- G3 Option 3 (rMD17/MD17) is a force-regression sanity check with no reaction,
  barrier, or dissociation limit; it cannot pass G3.
- Recommendation: run G3 Option 1 today; keep Option 2 as the first G4 pipeline test.

## G2d — the design

The world is $N$ particles in a 2D harmonic well. Each particle carries a hidden
phase $q_i$ that advances with time and local density,
$\dot q_i = \omega + \kappa \rho_i$, and contributes a force
$F_i^{\text{hidden}} = A[\cos q_i, \sin q_i]$. At fixed $q$ this force is the gradient
of a linear potential, so an energy model can represent it exactly. Because $q$ evolves
independently, the full system is non-conservative. The phase is not a function of the
current positions, so a stateless model cannot predict the hidden force; a model with
persistent per-particle state can infer $q_i$ from the first few displacements and
track it.

The first G2d condition sets the spring stiffness to zero. This removes pairwise
interactions and makes the true energy exactly per-particle, so the oracle is a clean
ceiling and a failure cannot be blamed on the perception layer. A second condition
with springs is the harder follow-up, not the first result.

All arms share the same neighbour perception (mean relative position, Gaussian density)
and the same MLP width. The arms are:

| Arm | Force source | State | Role |
|---|---|---|---|
| V1 | direct MLP force | no | NPA-style direct baseline |
| V2 | $-\nabla_x E(x)$ | no | strong stateless baseline |
| V3b | $-\nabla_x E(x,s)$ | per-particle, single net | the state hypothesis |
| V3b-sup | $-\nabla_x E(x,s)$ | per-particle, auxiliary probe | diagnostic: is state learnable? |
| Oracle | $-\nabla_x E(x,q)$ | true $q$ supplied | information ceiling, not a fair arm |

Training combines a short rollout position loss with a teacher-forced force loss. The
force loss is the decisive signal: on a position-only loss the hidden force is washed
out by the much larger well force. Metrics are rollout drift, final-step drift, force
MAE, and a linear probe $R^2$ from the latent state to $(\cos q,\sin q)$.

*(inference)* The expected result is Oracle < V3b < V2 ≈ V1 on force MAE, with V3b's
advantage shrinking on the parameter-shift stress test. A V3b result close to V2 would
mean the state is not learning the hidden phase, not that memory is useless; the
supervised probe distinguishes those cases.

> **In plain words.** Imagine a room of robot vacuums. Each one has a private,
> slowly turning dial that pushes it in a direction nobody can see. You only see where
> each vacuum is. A model with no memory can learn the room's shape but cannot know
> which way the hidden dial is pushing. A model with a scratchpad can watch the first
> few moves, guess each dial, and keep tracking it. That is the whole experiment.

## G2d — final status

The three-seed run is complete. V3b's mean force MAE is **0.833** against V2's
**0.923** (10% lower), with the oracle at **0.304**; V3b wins only one of three
seeds. Rollout drift is worse for V3b (**0.143** against **0.116**), and the state
probe reaches $R^2 \approx 0.26$. The single-seed 1,500-step slice that motivated
the multi-seed run reached 0.667 against 1.031, but that advantage did not survive
the larger sample. The full result and interpretation are in
[`11-g2d-results.md`](11-g2d-results.md).

*(measured)* Source: `runs/g2d_final/results.json` and `runs/g2d_v1_final/results.json`,
produced by `code/g2d_train.py` at 2026-11-09. CPU-only, $N=8$, 1,200 steps, rollout 16,
evaluation horizon 48, three seeds.

> **In plain words.** With three runs instead of one, the scratchpad's advantage
> shrinks to a small average that comes from a single lucky run, and its paths are
> consistently wobblier. The honest verdict is "not demonstrated", not "yes".

## G3 — what must be true

G3 is a scope gate, not an existential one. It asks whether the model can locate a real
barrier, respect rotational invariance, and recover the dissociation limit. The
reference reaction is H + H₂ → H₂ + H, the smallest reaction in chemistry: three
electrons, a classical barrier of **9.60 ± 0.02 kcal/mol** at the CBS limit
([Peterson, Woon and Dunning, 1994](https://doi.org/10.1063/1.466884)), and a collinear
D∞h saddle at $R(\mathrm{H-H}) = 0.930$ Å
([Dunning, 1994](https://doi.org/10.1016/0009-2614(94)87024-1)).

The gate is barrier MAE **< 1.5 kcal/mol**, rotational invariance **< 1e-4 eV**, and a
correct dissociation limit when the fragments are separated. A model trained on cheap
labels is evaluated on the expensive reference; the cheap and expensive levels are
reported with every number, as the writing contract requires.

> **In plain words.** G3 is the first time the model meets real quantum chemistry.
> We pick the simplest reaction there is, because if a model cannot get the simplest
> reaction right, the problem is the model, not the data.

## G3 Option 1 — self-generated H₃ with PySCF (recommended)

**Data.** Generate a collinear H₃ scan with PySCF 2.15.0: a reactant at large
separation, a symmetric saddle at 0.930 Å, and a grid of points between them. Label
each geometry at two levels: a cheap level (UHF/cc-pVDZ or a small DFT functional) for
training, and CCSD(T)/cc-pVTZ for the reference. *(The level probe in
`12-g3-results.md` later rejected UHF and B3LYP; the run uses CCSD(T)/cc-pVDZ as the
cheap level.)* Measured cost on four CPU threads is
17 s per geometry at cc-pVDZ, 26 s at cc-pVTZ, and 81 s at cc-pVQZ; a 30-point cc-pVTZ
scan is about 15 minutes, and a cc-pVQZ scan about 40 minutes
([PySCF CCSD docs](https://pyscf.org/user/cc.html)). The measured barriers are 10.21
(cc-pVDZ), 10.01 (cc-pVTZ) and 9.79 kcal/mol (cc-pVQZ), with a VTZ/VQZ CBS estimate of
9.63 against the literature 9.60. The final 14 × 14 scan gives 10.154 kcal/mol at
cc-pVDZ (see `12-g3-results.md`); the small difference is the probe geometry, not a
change of method.

**Model.** A small molecular energy model on the three pairwise H–H distances. Using
distances makes rotational and translational invariance exact by construction, so the
invariance test is a property of the representation, not a hoped-for symmetry. Train
V2 (stateless) as the main G3 model; include V3b as a stateful comparison only if time
allows, because static single-point energies give the latent state nothing to
integrate.

**Compute.** CPU only; no GPU and no download beyond `pip install pyscf`.

**Wall-clock.** Data generation about 15 minutes; model training minutes; evaluation
minutes. Fits inside one day.

**Risk.** Low. The main risks are basis/CBS bookkeeping and UHF convergence at large
separation; both are fixable with a fragment initial guess.

**What it proves.** It measures the G3 quantities directly: barrier height, invariance,
and dissociation limit. It does not test organic chemistry; that is G4.

> **In plain words.** We build the exam ourselves. Three hydrogen atoms, one simple
> reaction, and a free quantum-chemistry program that runs on the laptop. The model
> trains on cheap answers and is graded on expensive ones. No download, no GPU, no
> waiting for a cluster.

## G3 Option 2 — one Transition1x reaction

**Data.** Transition1x is one 6.62 GB HDF5 file (MD5
`faab0413cf6b042b6d50e6272dea9a8c`), MIT-licensed, with 10,073 reactions and 9.6 M
configurations at ωB97x/6-31G(d) with energies and forces
([figshare metadata](https://api.figshare.com/v2/articles/19614657);
[paper](https://doi.org/10.1038/s41597-022-01870-w)). Slice one reaction with `h5py`
from `data/<formula>/<rxn>/{reactant,transition_state,product}`.

**Model.** Train the same molecular energy model on a few thousand frames of one
reaction, hold out a different reaction family, and report barrier and reaction-energy
MAE.

**Compute.** CPU for training; the 6.6 GB download is the main cost. A free Kaggle GPU
is not required for one reaction, but the notebook path is documented for scale-up.

**Wall-clock.** Download plus slicing under an hour on a good link; training minutes to
hours depending on the model.

**Risk.** **Transition1x cannot supply H₃.** The published split metadata covers 170
formulas (https://figshare.com/ndownloader/files/36036280) and none is H-only. So this
option validates the pipeline on a real organic reaction but does not measure the G3
gate. It is the first G4 pipeline test, not a G3 substitute.

> **In plain words.** This is the real organic-chemistry dataset, but it has no
> hydrogen-only reaction. We can use it to prove the plumbing works on a real molecule,
> not to answer the H + H₂ question.

## G3 Option 3 — one rMD17 or MD17 molecule

**Data.** One molecule from rMD17 (67–175 MB per molecule, CC0,
[figshare](https://api.figshare.com/v2/articles/12672038)) or MD17 (about 90–360 MB per
molecule, CC BY 4.0, [sgdml](http://www.sgdml.org/#datasets)). Both include forces.

**Model.** The same molecular energy model, trained on energies and forces.

**Compute.** CPU or free GPU; small enough for a laptop.

**Wall-clock.** Minutes to load, hours to train a small model.

**Risk.** No reaction, no barrier, no dissociation limit. It is a force-regression
sanity check, useful for catching bugs in the molecular pipeline, but it cannot pass
G3.

> **In plain words.** This is like practising on a stationary bicycle when the exam is
> a road race. It is useful exercise, but it does not test the thing G3 cares about.

## Decision rule

| Option | Measures the G3 gate? | Compute | One-day? | Recommendation |
|---|---|---|---|---|
| 1. H₃ + PySCF | yes: barrier, invariance, dissociation | CPU | yes | **run today** |
| 2. Transition1x | no: no H-only formula | CPU / free GPU | yes, if download cooperates | first G4 pipeline test |
| 3. rMD17 / MD17 | no: no reaction | CPU / free GPU | yes | bug-check only |

Run Option 1 to close G3. Keep Option 2 queued as the first G4 step. Use Option 3 only
if the molecular pipeline needs a force-regression smoke test before Option 1.

> **In plain words.** Only the homemade hydrogen exam actually tests the hydrogen
> question. The other two are useful for different reasons, but calling either of them
> G3 would be marking the wrong exam.

## Open questions

- Does the V3b force advantage survive more seeds, or a better state update, given
  that the three-seed mean is carried by one seed?
- Does the molecular model need a learned equivariant representation, or are pairwise
  distances enough for three atoms?
- At what system size does the distance-only representation stop being sufficient?
- Does the CCSD(T)/cc-pVDZ label transfer generalise to a second reaction, or was H₃
  a lucky basis-set match?

> **In plain words.** The open questions are the ones the results cannot answer:
> whether the scratchpad's small average is real, whether the cheap-label trick
> generalises, and how far the distance-only model scales.

## What would change this document

- A cleaner multi-seed win for V3b, which would revive the state hypothesis before G4.
- A working public H₃ trajectory dataset with forces, which would remove the need to
  generate the reference.
- A G3 barrier error above 1.5 kcal/mol on a second reaction, which would make the
  pass a single-case result rather than a method result.

> **In plain words.** A cleaner multi-seed win for the scratchpad, a second reaction
> that fails, or a ready-made hydrogen dataset would each change the next step. The
> G2d result is in and is not a clean win; the G3 result is in and is a pass for one
> reaction.

## Sources

1. Peterson, Woon and Dunning, *Benchmark calculations with correlated molecular wave
   functions. IV*, J. Chem. Phys. 100, 7410 (1994).
   <https://doi.org/10.1063/1.466884> (retrieved 2026-11-09).
2. Dunning, *Gaussian basis sets for use in correlated molecular calculations*, J. Chem.
   Phys. 90, 1007 (1989); saddle geometry from the H₃ literature.
   <https://doi.org/10.1016/0009-2614(94)87024-1> (retrieved 2026-11-09).
3. Schreiner et al., *Transition1x*, Scientific Data 9, 2022.
   <https://doi.org/10.1038/s41597-022-01870-w> (retrieved 2026-11-09).
4. Transition1x figshare metadata.
   <https://api.figshare.com/v2/articles/19614657> (retrieved 2026-11-09).
5. PySCF CCSD documentation. <https://pyscf.org/user/cc.html> (retrieved 2026-11-09).
6. rMD17 figshare metadata. <https://api.figshare.com/v2/articles/12672038> (retrieved
   2026-11-09).
7. MD17 dataset page. <http://www.sgdml.org/#datasets> (retrieved 2026-11-09).
8. Project measurements: `runs/g2d_long1/results.json`, `code/g2d_train.py`,
   `npa/data/hidden_force.py`, `npa/models/mp_variants.py` (2026-11-09).
