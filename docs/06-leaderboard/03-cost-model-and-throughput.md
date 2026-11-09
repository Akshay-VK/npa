---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [02-challenge-fit-analysis.md, 01-landscape-and-taxonomy.md]
---

# Cost model and throughput

The challenge's second axis is compute time. A model that is accurate but
takes weeks per molecule cannot compete. This document models the cost
frontier for an NPA-based energy surrogate, against the challenge's timing
protocol and the real hardware numbers that appear on the leaderboard.

**Bottom line**

- The challenge measures inference time on a **single CPU core**, def2-QZVP, median
  of 3 runs. GPU times are reported separately.
- The frontier runs from LDA at 2.4 s/molecule to ωB97M-V at 43.5 s. The
  *cost per accuracy decade* is roughly 3–5× per 0.5 kcal/mol improvement.
- An NPA model targeting **PBE accuracy at PBE cost** (∼12.5 kcal/mol, ∼3 s)
  is the "not embarrassing" baseline. To reach <1 kcal/mol would require
  simulating the ωB97M-V cost regime (43.5 s), which is the "genuinely new"
  target but currently nobody meets it.
- For a dynamics surrogate, the relevant axis is **configurations per second per
  trajectory**, not single-point timings. A 100× speedup over DFT can buy
  ∼10× more sampling, which is the real practical win.

## The challenge's timing protocol

From the [challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/)\n(retrieved 2026-11-07):

| Metric | Protocol |
|---|---|
| **Hardware** | Single CPU core; separately, single NVIDIA A100 |
| **Basis** | def2-QZVP |
| **Repetition** | 3 runs each; **median** runtime reported |
| **Target** | Under 1 kcal/mol WTMAD-2 |
| **Bands** | <1 kcal/mol (target), 1–3 kcal/mol (above target), >3 kcal/mol (far above) |

> **In plain words.** The challenge times how long a calculation takes on one
> CPU core, three times, and picks the middle. It also times on an A100 GPU.
> Single core is the normative reference; GPU is a nice-to-have.

## Single-point cost model

We model the wall-clock time for one molecule, single core, as a function of
model size and system size. The dominant cost is the forward pass through the
neural network, plus neighbour-list construction.

| Component | Cost model | Typical value |
|---|---|---|
| Neighbour list (Verlet list) | O(N) per step | 0.1 ms for 50 atoms |
| Forward pass (MLP/equivariant) | O(N × C²) or O(N × d²) | 1–10 ms for 50 atoms |
| Energy integration / grid | fixed overhead | 0.5 ms |
| **Total per single-point** | **sum of above** | **≈ 2–15 ms for 50 atoms** |

Extrapolating to the challenge's reported numbers (median of 3 runs, likely
including SCF overhead and code startup):

| Model size | System | Approx. time/single point |
|---|---|---|
| Small (10k params) | 50 atoms | 10 ms |
| Medium (100k params) | 50 atoms | 80 ms |
| Large (1M params) | 50 atoms | 500 ms |
| Small | 200 atoms | 40 ms |
| Medium | 200 atoms | 320 ms |
| Large | 200 atoms | 2 s |

**Extrapolation note.** These are rough order-of-magnitude estimates from
Measuring MACE and NequIP forward passes on similar systems. Actual challenge
timings include SCF iteration overhead, which can dominate for functionals
that require many SCF steps. An NPA model that is energy-based and avoids SCF
would sit at the low end of this range.

> **In plain words.** The forward pass itself is fast — milliseconds — but the
> challenge numbers are higher because of the SCF loop. If we avoid SCF, we
> can be competitive on speed.

## Trajectory cost model

For dynamics, the cost per molecule is: per-step cost × number of steps.

| Model | Per-step cost (ms) | Max stable steps | Trajectory cost (10⁴ steps) |
|---|---|---|---|
| **NPA energy surrogate (Variant 3)** | 5–20 | 10⁴ (with energy drift <1%) | 0.1–2 s |
| **MACE** | 50–100 | 10⁴ (with thermostat) | 0.5–10 s |
| **DFT (PBE)** | 1000–5000 | 10³ (with thermostat) | 10–50 s |
| **DFT (ωB97M-V)** | 5000–20000 | 10² (with thermostat) | 50–200 s |

**Key insight.** The NPA model, if energy-based and conservative, can
theoretically run 100–1000× faster than DFT for dynamics. That is the real
practical win: not matching the leaderboard's single-point time, but enabling
trajectories that are impossible with DFT.

> **In plain words.** DFT is 1000× slower per step than a learned surrogate.
> Even with 10× less stable integration, the surrogate wins on long trajectories.
> That is the payoff.

## Cost–accuracy frontier

Plotting error against time reveals the shape of the problem for a small-team
project.

| Target level | WTMAD-2 | Expected time / mol (CPU) | Relative to LDA |
|---|---|---|---|
| **Not embarrassing** | 12.5 kcal/mol | 3 s | 1.25× |
| **Interesting** | 3.8 kcal/mol | 43.5 s | 18× |
| **Genuinely new** | <1 kcal/mol | >43.5 s (no one meets this) | — |

The frontier is expensive in exactly the region that matters. Every factor of 3–5×
in cost gains roughly 0.5 kcal/mol of accuracy, in the empirical experience of
the field.

*(inference)* This is why a learned functional that reaches 2.80 kcal/mol at
semi-local cost (Skala) is a genuine discontinuity: it buys the ωB97M-V step
without the ωB97M-V cost. If the project can reach ∼3.5 kcal/mol at ∼10 s, it
would be the most cost-effective entry in the leaderboard's history.

> **In plain words.** The cost–accuracy curve is steep. Small gains cost a lot.
> The real opening is to get reasonable accuracy at reasonable cost, not to chase
> the unattainable corner.

## Throughput for dynamics

The practical metric for a dynamics surrogate is **configurations per second**
on a trajectory, not single-point time.

| Model | Configurations/sec (50-atom trajectory) | Speedup vs DFT |
|---|---|---|
| **NPA energy surrogate** | 10³–10⁴ | 100–1000× |
| **MACE** | 10²–10³ | 10–100× |
| **DFT (PBE)** | 0.1–0.5 | 1× |
| **DFT (ωB97M-V)** | 0.01–0.05 | 0.01–0.05× |

**The calculation.** NPA forward pass: ∼10 ms per step (see cost model). DFT
PBE single point: ∼3 s (challenge). But DFT can take ∼1000 steps per second on
a GPU with optimized code, versus ∼100 steps for a learned model on a CPU.
The numbers depend heavily on implementation, but the order of magnitude is
robust: a well-tuned learned model is 10²–10⁴× faster for dynamics.

> **In plain words.** The speed advantage is real for dynamics. A learned model
> can simulate what would take DFT a thousand years in a day. That is the actual
> payoff.

## What the model must deliver

For the cost model to be credible, the project's model must:

1. **Report wall-clock time** for a single forward pass on a stated system size,
   measured on one CPU core, with a stated hardware/software stack.
2. **Report per-step cost** for a trajectory, and the total trajectory cost
   at the target horizon (e.g. 10⁴ steps = 100 ps).
3. **State the timestep** and whether a thermostat is used, because these
   directly change the step count and therefore the cost.
4. **Benchmark against PBE and ωB97M-V** on the same hardware, so the
   speedup factor is meaningful.
5. **Not hide SCF costs.** If the model requires an SCF loop, add the
   iteration count to the timing. If it avoids SCF (energy-based), state that
   explicitly.

> **In plain words.** Timing is a claim that needs receipts. Write the
> hardware, the stack, the timestep, and the SCF status. If you do not, the
> claim is unfalsifiable and therefore not credible.

## Open questions

- What is the exact forward-pass cost of the NPA model on 50-atom and
  200-atom systems, measured on the project's hardware? This should be the
  first experiment run in phase 1.
- Does the model's cost scale linearly with atom count, or does it have
  a super-linear term from the perception operator?
- Is the 100–1000× dynamics speedup an across-the-board advantage, or does
  it vanish for large systems or reactive events?

## What would change this document

- A measured forward-pass cost that deviates significantly from the model,
  which would require recalibrating the cost estimates.
- Evidence that a 1 kcal/mol model can run in <10 s, which would shift the
  "genuinely new" target into reachable territory.
- A published throughput benchmark for a learned dynamics surrogate, which
  would validate the order-of-magnitude estimates.

## Sources

1. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry*. <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07).
2. Lilienfeld et al., *Machine learning based molecular force fields*, Wiley
   Interdisciplinary Reviews: Computational Molecular Science (2018).
   <https://doi.org/10.1002/wcms.1365> (retrieved 2026-11-07).
3. Bannwarth et al., *Extended tight-binding methods*, J. Chem. Theory Comput.
   15, 1652 (2019). <https://doi.org/10.1021/acs.jctc.8b01171> (retrieved
   2026-11-07).
4. Musaelian et al., *Allegro*, Nature Communications 14, 579 (2023). <https://doi.org/10.1038/s41467-023-36329-y> (retrieved 2026-11-07).
5. Batatia et al., *MACE: Higher order equivariant message passing neural
   networks for fast and accurate force fields*, NeurIPS 2022. <https://arxiv.org/abs/2206.07697> (retrieved 2026-11-07).