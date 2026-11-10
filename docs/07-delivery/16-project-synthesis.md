---
status: draft
confidence: medium
last_verified: 2026-11-10
depends_on: [01-roadmap-and-kill-criteria.md, 05-g0-foundations-result.md, 07-g1-g2-results.md, 08-g2b-results.md, 09-g2c-results.md, 11-g2d-results.md, 12-g3-results.md, 13-g2e-results.md, 14-g4-plan.md, 15-g4-pipeline.md]
---

# Project synthesis: from 2D morphogenesis to a small reaction

This document answers one question: after running the whole NPA programme on a
CPU-only laptop — reproduction, latent-state tests on toys, a real-chemistry
barrier, and a real-reaction pipeline — what do we actually know, and what is the
honest verdict? It matters because the project spent its budget of experiments on
a specific hypothesis, that persistent latent state makes an energy model better
at dynamics, and the answer determines whether the state machinery is worth
carrying into larger systems.

**Bottom line**

- The reproduction is real: the pretrained NPA checkpoint reaches support-IoU
  **0.869** at 4,096 particles, against **0.124** for a random-init control
  [G0].
- Persistent latent state does **not** help on conservative or non-conservative
  toy systems, and on the one world built to make it necessary it lowers force
  error slightly but worsens rollout drift and never tracks the hidden phase
  (probe R² ≈ 0.30, below the 0.5 gate) [G2d, G2e].
- The state hypothesis is **not supported**. The improvements that do appear come
  from the residual parameterisation and EMA stability, not from phase tracking
  [G2e].
- G3 passes its three quantitative gates on H + H₂: barrier error
  **0.327 ± 0.037 kcal/mol** (< 1.5), rotational invariance
  **4.9 × 10⁻⁷ eV**, and a flat dissociation limit (0.032 kcal/mol at 20 Å)
  [G3].
- G4's pipeline runs end-to-end on a mock and on a small real slice, but the
  small-model barrier MAE is ~100 kcal/mol: **not competitive**, and the
  external baselines are still stubs [G4].
- The contribution of the project is the pipeline, the cheap-label lesson, and an
  honest negative result on state — not a competitive potential [G3, G4].

## G0 — reproduction of NPA 2D morphogenesis

G0 asked whether the official NPA code could be made to run and reproduce its
advertised behaviour on the only hardware available, a 32 GB laptop with an
integrated GPU and no CUDA. The answer is yes, with two patches: a pure-PyTorch
replacement for the CUDA-only `sphops` kernels, and a local copy of the target
image because the upstream emoji loader 404s. The pretrained lizard checkpoint
(10,880 parameters) was loaded unchanged and run with the official Euler update
for 120 steps at 1,024 particles and 150 steps at 4,096 particles.

The reproduction metric is support-IoU against the lizard mask. At 1,024
particles the pretrained model reaches **0.674** against **0.124** for an
identically seeded random-init control; at the paper's native 4,096 particles it
reaches **0.869**. The control never leaves the seed-cloud regime, so the result
is not a rendering artefact. Cost scales quadratically: **0.18 s/step** at 1,024
particles, **3.36 s/step** at 4,096, peaking at 3.8 GB RAM. Full-scale training
at 4,096 particles and batch 4 is not possible on this machine; full-scale
inference is.

> **In plain words.** We cooked the authors' recipe exactly as written, on a
> laptop with no graphics card, and the lizard shape grew. A control with an
> untrained brain did not grow it. The model genuinely learned the shape; the
> remaining question is whether the same machinery helps on anything harder.

## G1, G2, G2b and G2c — state does not help on conservative or non-conservative toys

G1 closed the training loop: a direct propagator (V1) recovers a known harmonic
force field to **force-MAE 0.0019** (threshold 0.01), so later numbers can be
trusted. G2 then tested the state hypothesis on a non-conservative oscillator
where a hidden spring stiffness k(t) varies in time. A single-network latent
model (V3b) tracks k(t) almost perfectly (r ≈ 0.99), but its energy MAE is
**0.2246** against the stateless V2's **0.0114**, and its rollout drift is
**0.2735** against **0.0166**. Perfect tracking did not translate into better
prediction.

G2b moved to a damped double well (Langevin dynamics, friction γ = 0.5). A
stateless model that directly sees velocity reaches **0.1876** force MAE
against V2's **0.2443**, so velocity information genuinely helps; but V3b's
learned latent state reaches **1.7180**, far worse than both. The state
mechanism, not the concept, is the bottleneck. G2c then validated the full NPA
machinery on multi-particle systems: V1 reproduces dynamics with **0.0028** and
**0.0031** rollout drift at N = 16 and N = 64, SPH perception helps about 2×
(0.0032 vs 0.0059), and state dimension (1 vs 16) makes no difference on a
conservative system, where there is nothing to remember.

> **In plain words.** On every toy where we tried to make memory useful, either
> the system was conservative and memory had nothing to do, or the system was
> non-conservative and the learned memory tracked the hidden variable yet failed
> to use it for prediction. A model that is simply told the velocity wins; a
> model that has to learn it loses.

## G2d and G2e — state helps force and drift, but not the hidden phase

G2d removed the "nothing to remember" excuse with an N = 8 multi-particle world
carrying a hidden per-particle phase q_i that drives a force. The arms share the
same perception; V2 is stateless, V3b carries a 4-dimensional per-particle
state, and an Oracle is given the true phase. Over three seeds, V3b's mean force
MAE is **0.833 ± 0.291** against V2's **0.923 ± 0.223** (a 10% mean
reduction), with the Oracle at **0.304 ± 0.006**. But V3b wins only one of three
seeds, its standard deviation (0.291) exceeds the mean gap (0.090), and its
rollout drift is worse on every seed (**0.143** vs **0.116**). A linear probe
recovers only R² ≈ 0.26 of the phase.

G2e then added three fixes — an EMA state update, a residual well removal, and a
phase anchor — plus a stateless history control V2H. The combined arm beats V2
and V2H on force MAE in all five seeds (**0.639** vs **1.123** and **0.887**)
and lowers drift (**0.079** vs **0.115** and **0.103**). But the state probe
still reaches only R² ≈ 0.30 (best arm 0.36), below the 0.5 gate, so the state
does not encode the phase. The improvements are consistent across four different
state updates, which points at the residual parameterisation and the EMA
stability rather than at phase tracking. The Oracle remains far ahead at
**0.384**, so the model class is also a bottleneck.

> **In plain words.** We gave the model a better scratchpad and a simpler target,
> and it got much better at predicting forces and staying stable in every seed.
> But when we checked whether the scratchpad actually remembers the hidden dial,
> it does not: about 30% of it. The model improved, but not because it learned
> the hidden state. The state behaves like a helpful regulariser, not a phase
> tracker.

## G3 — H + H₂ barrier from cheap labels

G3 is the first real-chemistry gate: can the molecular energy model predict the
barrier of the simplest reaction, stay rotationally invariant, and recover the
dissociation limit, using cheap labels? The reference is a self-generated
collinear H + H₂ → H₂ + H surface (14 × 14 grid, 196 geometries) computed with
PySCF 2.15.0 at CCSD(T)/cc-pVTZ, which gives a barrier of **10.010 kcal/mol**
against the literature complete-basis-set value of **9.60 ± 0.02**. A
distance-MLP (64-wide, two layers, 4,482 parameters) trained on CCSD(T)/cc-pVDZ
labels predicts **9.683 ± 0.037 kcal/mol**, a barrier error of
**0.327 ± 0.037 kcal/mol**, passing the 1.5 gate. The same model trained on
MP2/cc-pVTZ predicts **13.023 ± 0.270**, an error of **3.013 ± 0.270**, so
the negative control fails as it must. Rotational invariance is
**1.1 × 10⁻⁵ kcal/mol** (4.9 × 10⁻⁷ eV), exact by construction, and the
20 Å dissociation probe is flat to **0.031 kcal/mol**. The cheap-label lesson
is concrete: for H₃, "cheap" must mean the same correlated method in a smaller
basis; UHF, MP2 and B3LYP are wrong by 3–13 kcal/mol, not merely noisier.

> **In plain words.** We built the smallest real reaction on a laptop, calculated
> the true energy hill with an expensive method and a cheaper setting of the same
> method, and trained a small model on the cheaper one. It found the hill within
> a third of a unit, did not care how the molecule was turned, and did not run
> away when pulled apart. A model fed a deliberately bad method faithfully
> reproduced the bad method's mistake, which is what makes the pass meaningful.

## G4 — Transition1x pipeline

G4 is the "is it competitive?" gate on a real reaction dataset, Transition1x
(10,073 reactions, 9.6 M configurations, ωB97x/6-31G(d)). The first deliverable
is a pipeline test, not the competitive comparison. The loader, model
(`ReactivePairEnergy`, element-conditioned pairwise distances, forces via
autograd), training, metrics and baseline interface are built and tested on a
mock HDF5 that mirrors the real schema; **14 tests pass**. The real-data small
slice (3 train, 2 val, 8 test formulas) runs end-to-end, with barrier MAE
**116.6** (10 epochs, 32 hidden), **108.6** (50 epochs, 32 hidden) and
**99.4** (50 epochs, 128 hidden) kcal/mol, and force MAE ~2.9–4.1 eV/Å. These
numbers are far from chemical accuracy. The bottleneck is the atomization-energy
scale (~3000 eV) and the tiny model capacity; more epochs, larger models and
target normalisation are needed. The external baselines (MACE, UMA) are stubs,
and rollout stability and cost per trajectory are not yet measured on real data.

> **In plain words.** The plumbing works on a fake dataset and on a small real
> slice: you can load a reaction, train a model and compute the barrier error
> today. But the model currently misses the barrier by about a hundred units, so
> this is a pipeline result, not a competitive one.

## Verdict

The state hypothesis is **not supported**: on a world constructed to make
memory necessary, the latent state improves force MAE and rollout drift but never
tracks the hidden phase (R² ≈ 0.30 < 0.5), and the improvements are better
explained by the residual parameterisation and EMA stability than by phase
tracking. G3 passes its three quantitative gates on one three-atom reaction, with
the MP2 control failing as required, so the molecular pipeline and the
cheap-label strategy are validated. G4's pipeline runs end-to-end but is not
competitive (~100 kcal/mol barrier MAE). The honest contribution of the project
is therefore the reproducible pipeline, the cheap-label lesson (same correlated
method, smaller basis), the CPU-only reproduction of NPA 2D morphogenesis, and
an honest negative result on latent state — not a competitive potential or a
demonstrated memory mechanism.

> **In plain words.** We built a working chemistry pipeline and a faithful
> negative result. The memory idea did not earn its place, and the real-reaction
> model is not yet good enough to compete. What we are left with is solid
> engineering and an honest account of where the idea stops.

## Open questions

- Can a larger state dimension or a non-linear probe push the phase R² above 0.5,
  or is the phase not identifiable from positions at this resolution?
- Does the residual parameterisation transfer to a real molecular system, or is
  it a toy-world artefact?
- Does the 0.327 kcal/mol H₃ barrier error survive a second reaction and a true
  saddle optimisation, or is it a grid artefact?
- Can forces be learned to the same accuracy as energies? No force reference was
  generated for G3.
- Does target normalisation and larger capacity bring the G4 barrier MAE down
  from ~100 kcal/mol to something competitive?
- Does the latent state help at all on a reactive trajectory, where it has a
  history to carry?

> **In plain words.** The open questions are the ones the results cannot answer:
> why the state does not track the phase, whether the barrier result generalises,
> and whether the real-reaction model can be made competitive with more capacity
> and better normalisation.

## What would change this document

- A G2e variant reaching probe R² > 0.5 with improved or unchanged force and
  drift, which would revive the state hypothesis.
- A second reaction with barrier error above 1.5 kcal/mol, which would make the
  G3 pass a single-case result.
- A G4 model reaching competitive barrier MAE (within ~1.5 kcal/mol of the
  reference) at lower cost than the baselines.
- Evidence that the G4 ~100 kcal/mol result is a capacity or normalisation
  artefact rather than a method limit.
- A MACE or analytical-surface baseline clearly beating the model, which would
  move the project from "pass" to "not competitive" on G3.

> **In plain words.** If the state starts tracking the phase, if a second
> reaction fails, or if the real-reaction model becomes competitive, this
> conclusion changes. Until then, the honest labels are "state not supported" and
> "pipeline, not competitive".

## Sources

1. G0 reproduction: `docs/07-delivery/05-g0-foundations-result.md`;
   measurements `~/npa-work/logs/g0_check.json`, `g0_bench.jsonl`,
   hardware survey (2026-11-09). [G0]
2. G1/G2 results: `docs/07-delivery/07-g1-g2-results.md`;
   `runs/v1_harmonic/`, `runs/v2_harmonic_tv/`, `runs/v3b_harmonic_tv/`. [G1-G2c]
3. G2b results: `docs/07-delivery/08-g2b-results.md`; `runs/g2b/results.json`. [G1-G2c]
4. G2c results: `docs/07-delivery/09-g2c-results.md`; `runs/g2c_v1/metrics.json`. [G1-G2c]
5. G2d results: `docs/07-delivery/11-g2d-results.md`;
   `runs/g2d_final/results.json`, `runs/g2d_v1_final/results.json`. [G2d]
6. G2e results: `docs/07-delivery/13-g2e-results.md`; `runs/g2e/results.json`. [G2e]
7. G3 results: `docs/07-delivery/12-g3-results.md`;
   `runs/g3_h3/final.json`, `runs/g3_h3/*.npz`. [G3]
8. G4 plan and pipeline: `docs/07-delivery/14-g4-plan.md`,
   `docs/07-delivery/15-g4-pipeline.md`; `tests/test_transition1x.py`,
   `tests/test_g4_model.py`. [G4]
9. Roadmap and kill criteria: `docs/07-delivery/01-roadmap-and-kill-criteria.md`.
10. NPA repository, commit `1176ead09ef34e21814fd6b1dd29ca661aedb5da`,
    https://github.com/TheDevilWillBeBee/NPA (retrieved 2026-11-09).
11. Peterson, Woon and Dunning, *J. Chem. Phys.* **100**, 7410 (1994),
    https://doi.org/10.1063/1.466884 (retrieved 2026-11-09).
12. PySCF 2.15.0, https://pyscf.org (retrieved 2026-11-09).
13. Schreiner et al., *Transition1x*, Scientific Data **9**, 779 (2022),
    https://doi.org/10.1038/s41597-022-01870-w (retrieved 2026-11-10).
14. Writing contract: `docs/_meta/WRITING-CONTRACT.md`.