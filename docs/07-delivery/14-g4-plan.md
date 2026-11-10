---
status: draft
confidence: medium
last_verified: 2026-11-10
depends_on: [01-roadmap-and-kill-criteria.md, ../03-method-design/03-symmetry-equivariance-and-conservation.md, ../03-method-design/04-element-conditioning.md]
---

# G4 — Transition1x pipeline and competitive test

## Bottom line

- G4 is the roadmap's "Is it competitive?" gate: barrier MAE, reaction energy MAE,
  rollout stability, and cost per trajectory on a real reaction dataset.
- The first deliverable is a **pipeline test**, not the competitive comparison. The
  code runs end-to-end on a mock HDF5 today; the real run waits on the 6.6 GB
  Transition1x download.
- The model is a small element-conditioned pairwise-distance energy model with
  forces via autograd. It is stateless in the first pipeline; the latent state is
  added only if G2e passes.
- The official split is **formula-held-out** (150 train / 8 val / 8 test
  formulas), not reaction-family-held-out. The roadmap's wording is reconciled
  below.
- Baselines: UMA fine-tuned, MACE from scratch, PBE, and ωB97M-V on the
  reference values. The first pipeline test uses the reference values as the
  ceiling; the external baselines are Phase 2.

> **In plain words.** G4 is where the project meets the real competition. Before
> we can compete, the plumbing must work: load the data, train a small model,
> compute the right numbers, and run the baselines. That plumbing is built and
> tested on a fake dataset today. The real numbers arrive when the 6.6 GB file
> lands on disk.

## Dataset

Transition1x (Schreiner, 2022) is the source: `https://www.nature.com/articles/s41597-022-01870-w`,
dataset `https://figshare.com/articles/dataset/Transition1x/19614657`, code
`https://gitlab.com/matschreiner/T1x`.

Facts verified on 2026-11-10 from the figshare API and the T1x source code:

- One file `Transition1x.h5`: 6,623,929,000 bytes (6.62 GB), MD5
  `faab0413cf6b042b6d50e6272dea9a8c`, MIT-licensed.
- 10,073 reactions, 9.6M configurations, ωB97x/6-31G(d), elements H/C/N/O.
- Units: energy eV, forces eV/Å, positions Å. Convert eV to kcal/mol with
  23.0605.

### HDF5 schema

```
/
  data/
    <formula>/
      <rxn>/
        atomic_numbers                    (A,)
        positions                         (M, A, 3)
        wB97x_6-31G(d).energy             (M,)
        wB97x_6-31G(d).forces             (M, A, 3)
        reactant/   {same datasets, M=1, plus hash}
        product/    {same, M=1, plus hash}
        transition_state/ {same, M=1, plus hash}
  train/ <formula> -> /data/<formula>    (soft link)
  val/   <formula> -> /data/<formula>    (soft link)
  test/  <formula> -> /data/<formula>    (soft link)
```

The `data/<formula>/<rxn>` group holds the full path; the three named subgroups
are the endpoints. The transition state is the maximum-energy configuration along
the path (per `scripts/combine_dbs.py`). Barrier = E_ts − E_reactant; reaction
energy = E_product − E_reactant. Atomization energy = total energy minus the sum
of atomic reference energies (H −13.622, C −1029.413, N −1484.871, O −2041.840
eV, from `transition1x/dataloader.py`).

### Split

The official split is **formula-held-out**: 150 train formulas, 8 val, 8 test.
The `train`/`val`/`test` groups are soft links at the formula level, not at the
reaction level. The test formulas are `C3H5NO2`, `C2H5NO2`, `C2H3N3O2`,
`C2HNO3`, `C3H8N2O`, `C3HNO2`, `C5H5NO`, `C2HNO`.

The roadmap says "held-out reaction family, not a random split." The official
split holds out formulas, which is a proxy for reaction family (all reactions
sharing a formula). We use the official split and note the difference: a true
reaction-family holdout would require reaction-type labels, which the dataset does
not provide. If a family holdout is needed, it must be defined from the reaction
names or atom mappings.

### Filter

H/C/N/O only, ≤7 heavy atoms (heavy = Z > 1). All test formulas pass. The
loader asserts the element set and skips (or errors on) anything else.

## Model variants

The G2e arms (V1 direct, V2 stateless, V2H stateless history, V3b latent,
V3b-sup anchored, V3b-EMA, V3b-residual, V3b-combined, Oracle) are kept as
separate variants in all future experiments, so that each fix can be attributed
independently. The G4 energy model starts stateless; the latent state is added as
a separate arm only if G2e's verdict supports it.

## Model

`ReactivePairEnergy` in `npa/models/reactive.py`: element-conditioned pairwise
distance energy, variable atom count via a mask, E(3)-invariant by construction,
forces via autograd, smooth cutoff, per-element offset. Interface:
`energy(z, x, mask)` and `force(z, x, mask)`.

This matches ADR 0005 (shared trunk with element conditioning), not per-element
networks. The state is not in the first pipeline; it is added only if G2e
passes. The interface is kept compatible with a future state argument.

Training uses atomization energies to avoid large constants; forces are unchanged.

## Training and metrics

- Train on the official `train` formulas; validate on `val`; test on `test`.
- Loss: normalised energy MSE + λ_F × normalised force MSE. Adam; early stopping
  on val. A small model and a subset of frames for the first pass.
- Metrics: barrier MAE (kcal/mol), reaction energy MAE (kcal/mol), force MAE
  (eV/Å), rollout stability, cost per trajectory (s/force eval × steps, CPU).

### Rollout stability

The dataset has reaction paths, not time trajectories, so "rollout stability" is
defined as: integrate the model's forces from the reactant for a fixed number of
steps with a small timestep and report NaN/boundedness/energy drift. It is a
smoke test of the force field, not a physical MD validation.

## Baselines

- `ReferenceBaseline`: returns the dataset values. This is the ceiling (zero error).
- PBE, ωB97M-V: on the reference values (no extra calculation).
- MACE from scratch, UMA fine-tuned: external. Adapters are stubs with
  instructions; they need the respective packages and GPU time.

The first pipeline test uses the reference ceiling. The external baselines are
Phase 2.

## Phases

1. **Pipeline test (now, no download)**: loader, mock, model, training/eval,
   metrics, baseline interface, slice script, tests. End-to-end on the mock. Pass:
   mock tests green and a small real slice runs end-to-end with all metrics.
2. **Small real slice (after download)**: slice 3 train formulas + the 8 test
   formulas, train the small model, report force/barrier/reaction-energy MAE.
   Validates the pipeline on real data.
3. **Full G4**: all train formulas, baselines, rollout, cost. The competitive
   comparison.
4. **State (only if G2e passes)**: add the latent state to the model; compare to
   the stateless G4 model and the baselines.

## Pass / fail

Roadmap G4 pass: competitive barrier MAE with the fine-tuned baseline at ≥10×
lower inference cost, or better barrier MAE at equal cost. Kill: worse on both
accuracy and cost with no compensating advantage.

The pipeline-test pass is narrower and must not be confused with the G4 gate.

## Compute

- Zero budget. The download is the main cost (6.62 GB, college Wi-Fi).
- Training a small model is CPU-feasible; full G4 may need free GPU tiers.
- Runs and data are git-ignored.

## Open questions

- Whether the official formula split is sufficient for the roadmap's
  "reaction family" requirement, or whether a custom family split is needed.
- How many frames per reaction to use for training (full path vs. endpoints +
  stride).
- Whether the pairwise model generalises beyond H/C/N/O ≤7 heavy atoms.
- Whether to train on atomization energy or total energy.

## Sources

1. Schreiner, M. et al., *Transition1x*, Scientific Data 9, 779 (2022),
   `https://www.nature.com/articles/s41597-022-01870-w`, retrieved 2026-11-10.
2. Schreiner, M., Transition1x dataset, figshare v4,
   `https://doi.org/10.6084/m9.figshare.19614657.v4`, retrieved 2026-11-10.
3. T1x dataloader, `https://gitlab.com/matschreiner/T1x/-/raw/main/transition1x/dataloader.py`,
   retrieved 2026-11-10.
4. T1x combine_dbs, `https://gitlab.com/matschreiner/T1x/-/raw/main/scripts/combine_dbs.py`,
   retrieved 2026-11-10.
5. Roadmap, `docs/07-delivery/01-roadmap-and-kill-criteria.md`, Phase 4.
6. ADR 0005, shared trunk with element conditioning.
