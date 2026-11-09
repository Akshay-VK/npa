---
status: draft
confidence: high
last_verified: 2026-11-09
depends_on: [01-roadmap-and-kill-criteria.md, ../03-method-design/01-architecture-space.md]
---

# G0 — Foundations result: running NPA on a CPU-only laptop

G0 asks whether the official NPA code can be made to run and produce its
advertised behaviour. This document records the answer on the only hardware
available — a 32 GB laptop with an Intel integrated GPU and no CUDA — together
with the measured cost of every operation, so that later phases can be planned
against real numbers rather than vendor claims.

> **Bottom line**
> - The official repository is CUDA-only; it does not run unmodified on this
>   machine. A brute-force CPU replacement for its `sphops` kernels makes the
>   official model, weights and update rule run unchanged.
> - At 1,024 particles the pretrained lizard checkpoint reaches support-IoU
>   **0.674** against the target mask; an identically seeded random-init control
>   reaches **0.124**. At the paper's native 4,096 particles the same checkpoint
>   reaches **0.869**. The reproduction is real, not a rendering artefact.
> - Forward passes scale quadratically: 0.18 s/step at 1,024 particles,
>   3.36 s/step at 4,096, peaking at 3.8 GB of RAM. Full-scale *training* at
>   4,096 particles and batch 4 is not possible here; full-scale *inference* is.
> - Run everything in WSL2 on ext4. The Windows-mounted drive is 26× slower to
>   write, and cold small reads there run at about 1 MB/s, which matters for
>   environments, imports and checkpoints.
> - The upstream emoji loader is broken: its Noto URL now 404s because the
>   repository was reorganised. A local copy of the target image is required.

## What G0 had to prove

The roadmap defines G0 as "can we run the code?" with a days-scale budget and
two acceptable outcomes: proceed, or stop and fix tooling. It is not a science
gate. The point is to establish that the official implementation, its pretrained
weights and its update rule actually produce the paper's behaviour before any
of our own variants are built on top of them.

Three things therefore had to be demonstrated:

1. The model loads with the published parameter count.
2. The update rule moves a seed cloud towards the target morphology.
3. A control that has the same architecture and seed but none of the training
   does *not* do this.

> **In plain words.** Before trusting a recipe, you cook it once exactly as
> written. G0 is that first cook: does the official program, with the official
> weights, actually grow the shape it claims? And to be sure we are not fooling
> ourselves, we also run the same program with untrained weights — if that also
> produced the shape, the shape would be coming from our rendering, not from the
> model.

## The machine, measured

| Item | Value | Consequence |
|---|---|---|
| CPU | Intel Core Ultra 9 185H, 16 cores / 22 threads, AVX2 only | No AVX-512; BLAS-bound work is fine, SPH kernels are not |
| RAM | 32 GB physical; WSL2 sees 15 GB with 4 GB swap | Enough for 4,096-particle inference (3.8 GB peak), not for full training |
| GPU | Intel Arc integrated, driver 32.0.101.8132 | No CUDA, no `nvidia-smi`; the repository's kernels cannot compile |
| Disk | 912 GB free on ext4; 277 GB free on `C:` | Code, venv and checkpoints belong on ext4 |
| OS | Windows 10.0.26200; WSL2 kernel 6.18.33.2; Ubuntu 24.04.5 | WSL is the supported Linux build path |
| Power | Battery discharging at survey time | Sustained CPU runs will throttle; plug in for long jobs |

Measured I/O, 512 MiB sequential writes and reads:

| Path | Write | Read |
|---|---|---|
| ext4 (`~/npa-work`) | 1.1 GB/s | 8.1 GB/s |
| drvfs (`/mnt/d`) | 42.1 MB/s | — |

The drvfs figure is the decisive one. A 50 KB cold read from `/mnt/d` ran at
about 1.1 MB/s, which is roughly the cost of importing a Python package tree.
Virtual environments, the vendored repository and all run outputs therefore live
on ext4; only the Markdown documentation stays on the Windows-mounted drive.

> **In plain words.** The laptop's fast disk is the one inside Linux, not the
> one you see as `D:` in Windows. Reading files from `D:` is like fetching each
> page of a book from a warehouse instead of the shelf beside you. So the code
> and its working files go on the Linux side, and only the notes you read stay
> where Windows can see them.

## What we ran

The repository was cloned at commit
`1176ead09ef34e21814fd6b1dd29ca661aedb5da` and the CPU environment built with
PyTorch 2.15.0+cpu on Python 3.12. The official `sphops` package imports a
compiled CUDA extension at import time, so a replacement module installs the
authors' own `torch_sph.py` reference implementation under the same names
(`HashGrid`, `bin_particles`, `density`, `blur`, `gradient`,
`density_gradient`, `moment_matrix`, `gradient_hybrid`). No model code was
modified.

Three runs were performed:

- **Reproduction.** Load `data/pretrained/lizard.pth`, seed 1,024 particles from
  the official uniform-circle pool with seed 42, and apply the official Euler
  update for 120 steps using the paper's step schedule.
- **Control.** The same architecture, seed and schedule with freshly initialised
  weights.
- **Native-resolution check.** The same pretrained checkpoint at its training
  resolution of 4,096 particles, for 150 steps (pretrained only).

The metric is support-IoU: render the particles to a density image at the
adaptive resolution implied by the particle count (57×57 for 1,024 particles),
threshold both the render and the target alpha mask, and compute
intersection-over-union. Coverage is the fraction of pixels above threshold.

> **In plain words.** We took the authors' trained brain, dropped it into their
> own body, and let it grow. Then we did the same with an empty brain. We
> compare the resulting shape against the lizard silhouette the model was
> trained on, counting how much of the two shapes overlap.

## Results

| Run | Step 1 | Step 30 | Step 60 | Step 120 | Final coverage |
|---|---|---|---|---|---|
| Pretrained | 0.132 | 0.569 | 0.675 | 0.674 | 0.288 |
| Random init | 0.116 | — | — | 0.124 | 0.049 |

Target coverage is 0.312. The pretrained model reaches 0.674 IoU by step 60
and then plateaus; the control never leaves the seed-cloud regime. The gap is a
factor of 5.4 in IoU and a factor of 5.9 in coverage.

Parameter count from the checkpoint is **10,880**, consistent with the paper's
"about 11k" for the 2D model.

The same checkpoint at its native training resolution of 4,096 particles reaches
IoU **0.869** at 150 steps (coverage 0.302 against a target of 0.285), up from
0.148 at step 1. The model is therefore not only running but is *better* at the
resolution it was trained at, which is the expected direction and rules out the
possibility that the 1,024-particle number was a ceiling.

| Step | 1 | 30 | 60 | 90 | 120 | 150 |
|---|---|---|---|---|---|---|
| IoU (4,096 particles) | 0.148 | 0.660 | 0.795 | 0.844 | 0.867 | 0.869 |

Two caveats remain. First, IoU is a support metric and is insensitive to fine
structure; it answers "is the right region occupied?" not "is the shape
perfect?". Second, the 4,096 run is pretrained only — no random-init control at
that scale — because the control is uninformative once the pretrained result
is this far above the seed-cloud baseline (0.148 at step 1).

Cost per step on this machine, batch 1, 16 threads, forward only:

| Particles | Seconds/step | Peak RSS |
|---|---|---|
| 512 | 0.15 | 391 MB |
| 1,024 | 0.18 | 578 MB |
| 2,048 | 0.75 | 1.2 GB |
| 4,096 | 3.36 | 3.8 GB |

Training steps (forward plus backward) cost 0.019 s at 512 particles,
0.139 s at 1,024 and 0.64 s at 2,048. At 4,096 the feature-gradient tensor alone
is about 2.1 GB before autograd saves anything, so a training step at batch 4
would need tens of gigabytes. This is the hardware wall.

> **In plain words.** The model can *watch* a 4,096-particle simulation on this
> laptop at about three seconds per frame, which is fine for a few hundred
> frames. It cannot *learn* at that size, because learning needs to remember
> every intermediate number from every frame, and that does not fit in memory.

## Where each phase will run

| Workload | Machine | Why |
|---|---|---|
| G0 reproduction and inference | Local WSL2, CPU | Runs in minutes; no quota, no upload, fully reproducible |
| Phase 1 toolchain and toy experiments (≤1,024 particles) | Local WSL2, CPU | Measured at 0.14 s per training step; iteration is interactive |
| Full-scale 2D training (4,096 particles, batch 4) | Free Colab T4 or Kaggle GPU | The official notebook targets a 16 GB T4; local memory is insufficient |
| Real-chemistry phases (3+) | Free GPU for training; local CPU for evaluation | Depends on dataset size; revisit at G3 |

Colab's free tier gives a T4 with roughly 12-hour sessions and no persistent
disk; Kaggle gives about 30 GPU-hours per week with 9-hour sessions and
persistent datasets. Kaggle is the better default for anything that must resume.
Neither is needed for G0.

Zero budget is therefore not a blocker at G0 or phase 1. It becomes a
scheduling constraint only when a single training run exceeds one free session.

> **In plain words.** Small experiments fit on the laptop. The one big training
> job the paper describes needs a free cloud GPU, which is available but comes
> in timed slices. We only pay that cost when we actually need to train at the
> paper's scale, and the authors' own checkpoint lets us skip it for the
> reproduction.

## Upstream breakages and local patches

Two defects in the official repository were found and worked around:

1. **`sphops` is CUDA-only.** `sphops/__init__.py` imports the compiled
   extension at module load. There is no CPU fallback, despite the repository
   shipping a pure-PyTorch reference implementation used by its own tests.
2. **The emoji loader 404s.** `utils/loader.py` fetches Noto emoji from
   `png/512/...`; the repository now stores them under `2D/png/512/...`. The
   target image is downloaded once and passed as a local path.

Both are recorded so that a future reader does not mistake them for our bugs.

> **In plain words.** The authors' program assumes a particular kind of graphics
> card and fetches its reference picture from a shelf that has since been moved.
> Neither is our mistake, and both are easy to patch: we supply our own
> equivalent of the graphics-card instructions and keep a local copy of the
> picture.

## Open questions

- How much of the 0.869 ceiling is the metric rather than the model? A
  chamfer-distance or Wasserstein metric would separate "right region, wrong
  detail" from "wrong region".
- Is the CPU shim numerically identical to the CUDA kernels, or only close? The
  repository's own `test.py` compares the two implementations and should be run
  on a CUDA machine before any result is published.
- Does the plateau hold or improve past 150 steps at 4,096 particles? The
  trajectory was still rising (0.844 at 90, 0.869 at 150).

## What would change this document

- A CUDA machine becoming available, which would make the shim unnecessary and
  let the official test suite run.
- Evidence that the free GPU tiers cannot sustain a 4,096-particle training run,
  which would force a smaller-scale protocol for phase 2.
- A 4,096-particle run past 150 steps showing degradation (overfitting or
  collapse), which would bound the useful rollout length.

## Sources

1. TheDevilWillBeBee, *NPA: Neural Particle Automata*, GitHub repository,
   commit `1176ead09ef34e21814fd6b1dd29ca661aedb5da`,
   https://github.com/TheDevilWillBeBee/NPA (retrieved 2026-11-09).
2. *Neural Particle Automata: Learning Self-Organizing Particle Dynamics*,
   SIGGRAPH 2026, arXiv:2601.16096,
   https://arxiv.org/abs/2601.16096 (retrieved 2026-11-09).
3. Google Fonts, *Noto Emoji*, `2D/png/512/emoji_u1f98e.png`,
   https://raw.githubusercontent.com/googlefonts/noto-emoji/main/2D/png/512/emoji_u1f98e.png
   (retrieved 2026-11-09).
4. Project measurements, 2026-11-09: `~/npa-work/logs/g0_check.json` (IoU and
   coverage), `~/npa-work/logs/g0_bench.jsonl` (timings and peak RSS), and the
   hardware survey recorded above. These are first-party measurements, not
   external claims.
