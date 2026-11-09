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

**Status.** G0 closed: the official model and weights reproduce their 2D
morphogenesis demo on a CPU-only laptop (IoU 0.869 at 4,096 particles). Full
write-up: `docs/07-delivery/05-g0-foundations-result.md`.

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

G0 (run the code) — done. G1 (does the loop close) — next. G2 (does state
help?) — the existential gate. Full roadmap and kill criteria:
`docs/07-delivery/01-roadmap-and-kill-criteria.md`.

## License

Code: MIT. Documentation: CC-BY-4.0. (Set before first external contribution.)