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

**Status (2026-11-10).** G0 reproduced NPA 2D morphogenesis on CPU (IoU 0.869 at
4,096 particles). G3 passed: a 4,482-parameter distance-MLP trained on
CCSD(T)/cc-pVDZ predicts the H + H₂ barrier to **0.327 ± 0.037 kcal/mol**
against a CCSD(T)/cc-pVTZ reference (10.010 kcal/mol), with rotation 4.9e-7 eV
and 20 Å dissociation 0.032 kcal/mol. G2e: the latent state is **capacity-limited
but supported at sufficient size** on the hidden-phase toy — R² 0.302 at
`state_dim=4` but R² **0.706** at `state_dim=16` (5 seeds, independently
verified), with force MAE 0.581 and drift 0.073. G4 pipeline runs on mock and
real Transition1x slices but is not competitive (~100 kcal/mol barrier MAE).
Full synthesis: `docs/07-delivery/16-project-synthesis.md`. Blog visuals:
`docs/07-delivery/blog/index.html`. Full write-ups:
`docs/07-delivery/05-g0-foundations-result.md`,
`docs/07-delivery/12-g3-results.md`,
`docs/07-delivery/13-g2e-results.md`,
`docs/07-delivery/14-g4-plan.md`,
`docs/07-delivery/15-g4-pipeline.md`.

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

G0 (run the code) — done. G1/G2 (does state help?) — done on conservative and
non-conservative toys; G2d/G2e shows a capacity-limited but supported state
result on the hidden-phase toy (R² 0.706 at state_dim=16). G3 (one real
reaction) — passed. G4 (is it competitive on Transition1x?) — pipeline built and
tested; current model not competitive (~100 kcal/mol). Project synthesised and
closed as a reproducible, honest result. Full roadmap and kill criteria:
`docs/07-delivery/01-roadmap-and-kill-criteria.md`. Synthesis:
`docs/07-delivery/16-project-synthesis.md`.

## License

Code: MIT. Documentation: CC-BY-4.0. (Set before first external contribution.)