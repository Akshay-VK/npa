---
status: draft
confidence: high
last_verified: 2026-11-10
depends_on: [14-g4-plan.md, ../03-method-design/03-symmetry-equivariance-and-conservation.md]
---

# G4 pipeline: what is built and tested

## Bottom line

- The G4 data pipeline, model, training, and metrics are built and tested on a
  mock HDF5 that mirrors the real Transition1x schema exactly.
- 14 tests pass: mock schema, loader, filter, split, barrier/reaction energy,
  MD5 helper, model invariance, force consistency, smoke train.
- A final real-data run on `Transition1x_mid.h5` now exists (see Baseline
  comparison): barrier MAE 106.1 kcal/mol, reaction energy MAE 91.4 kcal/mol,
  force MAE 3.10 eV/Å. The mock numbers are still not a result.

> **In plain words.** The plumbing works on a fake dataset. You can load a real
> reaction, train a small model, and compute the barrier error today, as soon as
> the file is on disk. The numbers will not be meaningful until the full training
> runs, but the code will not be the blocker.

## What is built

- `npa/data/transition1x.py`: loader, filter, split, barrier/reaction-energy
  helpers, MD5 verifier, `Transition1xDataset`, collate, `make_mock_hdf5`.
- `npa/models/reactive.py`: `ReactivePairEnergy`, element-conditioned pairwise
  distance energy, variable N, E(3)-invariant, forces via autograd.
- `code/g4_train.py`: CLI with `--mock` smoke mode, training, eval, metrics.
- `code/g4_slice.py`: copy selected formulas into a small HDF5.
- `tests/test_transition1x.py`, `tests/test_g4_model.py`: 14 tests, all green.

### Test command

```bash
.venv/bin/python -m unittest tests.test_transition1x tests.test_g4_model -v
```

### Mock smoke command

```bash
.venv/bin/python code/g4_train.py --mock --epochs 3
```

This writes `runs/g4_mock/metrics.json`.

### Real-data smoke (small slice, 3 train + 2 val + 8 test formulas)

| Config | Epochs | Hidden | Barrier MAE (kcal/mol) | Reaction energy MAE (kcal/mol) | Force MAE (eV/Å) | Time |
|---|---|---|---|---|---|---|
| small | 10 | 32 | 116.6 | 150.8 | ~4.1 | 1.5 s |
| small | 50 | 32 | 108.6 | 121.1 | 3.6 | 3.9 s |
| large | 50 | 128 | 99.4 | 105.3 | 2.9 | 6.3 s |

The model learns slowly: 50 epochs with 128 hidden units reach 99 kcal/mol barrier
MAE, still far from chemical accuracy. The bottleneck is the atomization-energy
scale (~3000 eV) and the tiny model capacity. The pipeline works; the real G4
comparison needs more epochs, larger models, and target normalisation.

## Exact commands after download

1. Verify the file (see `notes/transition1x-download.md`).
2. Slice a small subset for CPU iteration:

```bash
.venv/bin/python code/g4_slice.py \
  --input ~/npa-work/data/Transition1x.h5 \
  --output ~/npa-work/data/Transition1x_small.h5
```

3. Train on the small slice:

```bash
.venv/bin/python code/g4_train.py \
  --data ~/npa-work/data/Transition1x_small.h5 \
  --epochs 50 --max-frames 8
```

4. Train on the full file (needs time and possibly free GPU):

```bash
.venv/bin/python code/g4_train.py \
  --data ~/npa-work/data/Transition1x.h5 \
  --epochs 50 --max-frames 8 --out runs/g4_full
```

## What is not built yet

- The external baselines (MACE, UMA) are stubs with instructions.
- Rollout stability and cost-per-trajectory reporting are defined but not yet
  measured on real data.
- The metadynamics free-energy profile (roadmap item 5) is out of scope for the
  pipeline test.
- The latent state is not in the model; it is added only if G2e passes.

## Limitations

- The mock numbers are not a result. The mock uses a toy energy, and the model
  has not seen real chemistry.
- The official split is formula-held-out, not reaction-family-held-out. The
  roadmap's "reaction family" wording is reconciled in `14-g4-plan.md`.
- Force MAE on the mock is not comparable to the G3 force numbers (different
  systems, different units).

## Baseline comparison

Final G4 run on `Transition1x_mid.h5` (50 epochs, 8 frames, hidden 512):
`runs/g4_final/metrics.json`.

| Method | Barrier MAE (kcal/mol) | Reaction energy MAE (kcal/mol) | Force MAE (eV/Å) |
|---|---|---|---|
| Our model (G4 final) | 106.1 | 91.4 | 3.10 |
| Dataset reference (wB97x/6-31G(d) labels) | 0 (by definition) | 0 (by definition) | 0 (by definition) |
| MACE (published) | ~0.5-1.1 | not reported | not reported |

Published MACE numbers are from the 2026 HAT-in-peptides work
(DOI 10.1038/s41524-026-02335-z; PMC13054793) and MACEPre-DeePEST
(chemrxiv DOI 10.26434/chemrxiv.15009333/v1). Our model is not competitive
with these published potentials on barrier MAE. The contribution of this work
is the end-to-end pipeline (data loading, filtering, training, metrics), not
the accuracy of this small baseline model.

## Sources

1. Plan, `docs/07-delivery/14-g4-plan.md`.
2. Roadmap, `docs/07-delivery/01-roadmap-and-kill-criteria.md`, Phase 4.
3. Download instructions, `docs/07-delivery/notes/transition1x-download.md`.
