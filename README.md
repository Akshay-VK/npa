# npa — Neural Particle Automata for fast, stable, reactive molecular dynamics

**The problem.** Molecular dynamics is too slow for reactive chemistry: a
single reactive trajectory can take weeks on a supercomputer, and the tools
that are fast (classical force fields) cannot break bonds. This project asks
whether a learned particle automaton — NPA, from SIGGRAPH 2026 — can be turned
into a general energy-based dynamics engine that is fast, stable over long
rollouts, and handles bond breaking.

**The bet.** NPA learns attractors. Chemistry is not an attractor problem.
The interesting question is whether a *persistent latent state* plus an
*energy-based* (not direct-update) formulation fixes that, or whether it
collapses. That experiment is G2, and it is the only existential gate.

**Status (2026-11-10).** G3 passed: a 4,482-parameter distance-MLP trained on
CCSD(T)/cc-pVDZ labels predicts the H + H₂ barrier to **0.327 ± 0.037 kcal/mol**
against a CCSD(T)/cc-pVTZ reference of 10.010 kcal/mol. Rotational invariance is
4.9e-7 eV and the 20 Å dissociation error is 0.032 kcal/mol. Full write-up:
`docs/07-delivery/12-g3-results.md`.

G2e ran: the combined fix (EMA state + residual well) beats the stateless V2 and
the stateless history control in all 5 seeds on force MAE (0.639 vs 1.123 and
0.887) with lower drift (0.079 vs 0.115). But the state probe R² is 0.30, below
the 0.5 threshold, so the state hypothesis is not supported. Full write-up:
`docs/07-delivery/13-g2e-results.md`.

G4 pipeline is built and tested on a mock HDF5 (14 tests green) and runs
end-to-end on the real 6.6 GB Transition1x file. A small slice (3 train + 2 val +
8 test formulas) trains in seconds. Full G4 comparison is next. Full write-up:
`docs/07-delivery/14-g4-plan.md` and `docs/07-delivery/15-g4-pipeline.md`.

G0 closed: the official model and weights reproduce their 2D morphogenesis demo on
a CPU-only laptop (IoU 0.869 at 4,096 particles). Full write-up:
`docs/07-delivery/05-g0-foundations-result.md`.

G0 closed: the official model and weights reproduce their 2D morphogenesis demo on
a CPU-only laptop (IoU 0.869 at 4,096 particles). Full write-up:
`docs/07-delivery/05-g0-foundations-result.md`.

## Zero budget

Everything here runs on a 32 GB laptop (WSL2) and free GPU tiers (Kaggle first,
Colab as fallback). No paid compute, no paid software. If a run does not fit
in 15 GB of RAM or one free session, it is redesigned, not purchased.

## Quick start

```bash
git clone https://github.com/Akshay-VK/npa
cd npa
# heavy deps live on ext4, not in the repo:
python3 -m venv .venv && .venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt  # coming in v0.0
python -m npa train configs/v0_oracle.yaml --seed 0
```

The G0 reproduction scripts live in `code/` (see `code/README`-equivalent notes
in `~/npa-work/README.md` on the original machine).

## Layout

Deep modules, small interfaces. See the codebase-design notes in
`docs/` for the reasoning.

- `npa/core/` — perception (`sph`) and the stepper (`sim`). The only modules
  the trainer touches.
- `npa/models/` — one module per variant (V0 oracle, V1 direct, V2 energy,
  V3a relaxed, V3b latent). All satisfy `DirectDynamics` or `EnergyModel`.
- `npa/data/` — synthetic worlds, generated on the fly.
- `npa/train/` — one loop for every variant.
- `npa/eval/` — metrics and the physics test battery.
- `docs/` — the research documentation set (39 files, ~67k words).
- `code/` — G0 tooling (CPU shim, benchmarks, reproduction).

## Roadmap

G0 (run the code) — done. G1/G2 (does state help?) — done; state does not help on
the conservative and non-conservative toys. G2d — inconclusive; G2e is the
follow-up. G3 (one real reaction) — passed. G4 (is it competitive on Transition1x?)
— next; the pipeline is built, the real-data run waits on the 6.6 GB dataset. Full
roadmap and kill criteria: `docs/07-delivery/01-roadmap-and-kill-criteria.md`.

## License

Code: MIT. Documentation: CC-BY-4.0. (Set before first external contribution.)