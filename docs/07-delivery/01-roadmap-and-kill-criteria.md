---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [../00-orientation/01-project-charter.md, ../08-risk/01-risk-register.md]
---

# Roadmap and kill criteria

A roadmap without stop rules is a wish list. This document defines six phases,
each with a question, a cheap test, a pass condition written *before* the
experiment, and a kill criterion. The phases are ordered by cost, not by
ambition: the cheapest experiment that can invalidate the project runs first.

**Bottom line**

- Phase 2 (toy world, force-vs-endpoint loss) is the decision point. It costs
  days and can kill the architecture.
- Nothing before phase 5 requires DFT at scale. Phases 0–2 are synthetic.
- Every phase produces a versioned artefact: `v0.1`, `v0.2`, … so iteration 2
  cannot silently inherit iteration 1's bugs.
- Kill criteria are not failure. A documented "no" at phase 2 is a publishable
  transferability result.
- The roadmap is deliberately front-loaded with the experiments that are
  embarrassing to discover late.

## The versioning scheme

Three independent version numbers, because conflating them is how projects lose
track of what changed:

| Version | What it tracks | Bumps when |
|---|---|---|
| **Model version** `mN` | Architecture + weights | Any change to the network, loss, or training data |
| **Harness version** `hN` | Evaluation protocol | Any change to splits, metrics, or baselines |
| **Data version** `dN` | Dataset + manifest | Any change to labels, filtering, or deduplication |

A result is always reported as `mN / hN / dN`. If any changes, the comparison is
invalid and must be re-run. This is the single cheapest discipline in the
project and the one most often skipped.

*(inference)* The reason this matters more here than in typical ML work: the
deliverable is a *physical* claim, and physical claims are sensitive to
protocol in ways that image benchmarks are not. A different cutoff or a
different basis set is a different experiment.

> **In plain words.** Three separate counters: one for the model, one for how
> you grade it, one for the data. Write all three on every result. If the
> grading or data changed, you cannot compare the scores.

## Phase 0 — Foundations (days)

**Question.** Do we understand the problem and can we run the code?

**Do.**
1. Read the five Tier-1 sources in
   [the bibliography](../09-sources/01-annotated-bibliography.md).
2. Reproduce the NPA 2D morphogenesis demo from the official code.
3. Stand up the repository: config system, seed control, logging, one GPU.
4. Archive the challenge page and leaderboard with checksums (done; see
   [`09-sources/evidence/`](../09-sources/evidence/retrieval.json)).

**Pass.** The demo trains and produces the expected shape from a seed. The
repository reproduces a run from a config file alone.

**Kill.** The demo cannot be reproduced within a week — which would indicate a
tooling or documentation problem serious enough to block everything.

**Artefact.** `v0.0-foundations`: environment lockfile, reproduction notes,
baseline demo checkpoint.

> **In plain words.** Before inventing anything, prove you can run someone
> else's code and get their result. If you cannot, you are not ready to build.

## Phase 1 — Toolchain on a synthetic potential (1–2 weeks)

**Question.** Can the whole loop — data, training, rollout, evaluation —
work end to end on a system where the right answer is known exactly?

**Do.**
1. Implement a 2D two-species particle system with an analytic potential
   (Lennard-Jones plus a Gaussian barrier, or a double well with a known
   saddle).
2. Train three models on it:
   - **M1:** direct position update (Variant 1).
   - **M2:** energy + autodiff forces, no latent state (Variant 2).
   - **M3:** energy + autodiff forces + persistent latent state (Variant 3).
3. Instrument: energy drift, momentum, barrier height, reaction rate,
   rollout stability.
4. Run the [physics test battery](../05-evaluation/03-rollout-stability-and-physics-tests.md).

**Pass.** All three models train without divergence; M2 conserves energy to
<0.1% over 10⁴ steps; the harness reports every metric for every model from a
single command.

**Kill.** M2 cannot conserve energy on a potential where conservation is
guaranteed by construction — which would mean the integrator or the force
computation is wrong, not the architecture.

**Artefact.** `v0.1-toolchain`.

> **In plain words.** Build the whole factory on a toy product first. If the
> factory cannot make a toy correctly, it will not make a real one.

## Phase 2 — The decision experiment (1 week)

**Question.** Does persistent latent state buy anything, and does attractor
training suppress reactions?

This is the phase the project exists to run. Everything before is setup;
everything after is conditional on the answer.

**Do.** Four arms on the same toy potential, same data, same parameter budget,
same compute budget:

| Arm | Loss | State | Purpose |
|---|---|---|---|
| **A** | Endpoint only | yes | The NPA-style baseline |
| **B** | Endpoint only | no | Isolates the state contribution |
| **C** | Per-step energy + force | yes | The proposed design |
| **D** | Per-step energy + force | no | The strong local baseline |

**Measure.**
1. Barrier-crossing rate at a fixed temperature, versus ground truth.
2. Time-to-first-crossing distribution.
3. Energy drift over 10⁴ steps.
4. Rollout position error at horizons 1, 10, 100, 1000.
5. Whether perturbed trajectories return to the reactant (the regeneration
   test — a *failure* here is good for chemistry).

**Pass (for the architecture).** C beats D on rollout error and barrier-crossing
rate at equal parameter count, with non-overlapping confidence intervals
across ≥5 seeds.

**Pass (for the science).** A exhibits suppressed barrier crossing relative to
C, on the same potential, reproducibly. This is worth publishing whether or not
C is better than D.

**Kill.** If C ≈ D on both metrics after a genuine tuning effort, persistent
state has no measurable benefit in the simplest possible setting. Stop and
write it up as a negative result; do not proceed to real chemistry hoping it
appears at scale.

> **In plain words.** Four versions of the same model, one difference each.
> If memory does not help even here, it will not help anywhere. This is the
> cheapest possible place to be wrong.

**Why this is a fair test.** Equal parameters, equal compute, equal data, same
potential, ≥5 seeds. If the result depends on tuning, tune both arms equally
and report the tuning budget.

## Phase 3 — One real reaction (2–4 weeks)

**Question.** Does any of it survive contact with real electronic structure?

**Do.**
1. Choose H + H₂ → H₂ + H (three electrons, exactly solvable barrier,
   well-characterised). Generate a small reference set with a high-level method
   and a cheap one.
2. Train M2 and M3 on the cheap labels, evaluate on the expensive ones.
3. Compare against: a fitted analytical surface, a small MACE model, and the
   cheap method itself.
4. Rotate the whole system by random quaternions and verify invariance.
5. Separate the fragments to 20 Å and verify the dissociation limit.

**Pass.** Barrier height within 1.5 kcal/mol of the reference; rotational
invariance to <1e-4 eV; correct dissociation limit.

**Kill.** The model cannot locate the barrier at all, or fails rotational
invariance after an honest attempt at an equivariant formulation.

**Artefact.** `v0.2-h3`.

> **In plain words.** Try one real reaction before trying ten thousand. If the
> model cannot get the simplest reaction in chemistry right, the problem is the
> model, not the data.

## Phase 4 — Organic reaction chemistry (1–3 months)

**Question.** Is it competitive with pretrained baselines on a real reaction
dataset?

**Do.**
1. Train on a Transition1x subset (H/C/N/O, ≤7 heavy atoms).
2. Evaluate on a **held-out reaction family**, not a random split.
3. Baselines: UMA fine-tuned, MACE trained from scratch, PBE, ωB97M-V
   (on the reference values).
4. Report barrier MAE, reaction energy MAE, rollout stability, and cost per
   trajectory.
5. Run one enhanced-sampling experiment (metadynamics on a single reaction) and
   compare the free-energy profile to DFT.

**Pass.** Competitive barrier MAE with the fine-tuned baseline at ≥10× lower
inference cost, or better barrier MAE at equal cost.

**Kill.** Worse on both accuracy and cost with no compensating advantage
(interpretability, parameter count, or stability). Document and stop, or pivot
to the benchmark contribution.

**Artefact.** `v1.0-transition1x`.

> **In plain words.** This is where the project meets the real competition.
> Beat it on one axis and tie on the other, or explain what else you offer.

## Phase 5 — The optional extension (open-ended)

**Question.** Is there a challenge-shaped or benchmark-shaped contribution?

Two routes, both gated:

**Route A — functional-adjacent.** Test whether persistent state or a different
mixing topology improves Skala's non-local module. Requires modifying a DFT
code and a CCSD(T)-quality dataset. High cost, high credibility.

**Route B — benchmark.** Build and release a reactive-dynamics benchmark with
fixed splits, reference trajectories, and metrics. Lower technical risk, real
community value, and it makes the project citable even if the model is not
better.

**Decision rule.** Choose Route B unless Route A has a collaborator who already
owns a DFT code integration. Route A without that collaborator is a year of
plumbing.

> **In plain words.** Two ways to matter beyond the model: improve the thing
> the competition asked for, or build the exam everyone else will use. The
> second is cheaper and more likely to succeed.

## The gate table

| Gate | Question | Decision | Cost if wrong |
|---|---|---|---|
| G0 | Can we run the code? | proceed / fix tooling | days |
| G1 | Does the loop close? | proceed / fix engineering | weeks |
| G2 | **Does state help?** | **proceed / publish negative** | **the project** |
| G3 | Does it survive one real reaction? | proceed / fix physics | month |
| G4 | Is it competitive? | proceed / pivot to benchmark | months |
| G5 | Is there a story? | write / stop | — |

Only G2 is existential. Everything else is a scope decision.

## What "done" looks like

A defensible end state has all of:

1. A repository that reproduces every figure in the paper from config files.
2. A verification log with a source for every external number.
3. A baseline table including the strongest cheap and expensive competitors.
4. A stated domain, with the failure boundary drawn honestly.
5. A written negative result for anything that did not work.

That is achievable even if the architecture loses at G2 — which is the point of
ordering the phases this way.

## Open questions

- Is the phase-2 toy world rich enough to be informative? A single barrier may
  be too easy; two competing channels may be better. See
  [experiment protocols](02-experiment-protocols.md).
- How much tuning counts as "a genuine effort" before declaring a null result?
  Propose: equal hyperparameter search budget, measured in GPU-hours, reported.
- Should phase 4 start from a pretrained model or from scratch? From scratch is
  the honest architecture test; pretrained is the competitive one. Run both if
  budget allows.

## What would change this document

- Phase 2 producing a strong positive result, which would justify compressing
  phases 3–4.
- Phase 2 producing a null result, which would redirect effort to phase 5
  Route B.
- A published reactive benchmark appearing, which would replace phase 5
  Route B with adoption.

## Sources

Phase durations are estimates, not sourced facts. The physical constraints
behind them are in [reaction kinetics](../01-science/04-reaction-kinetics-and-rare-events.md)
and [compute budget](04-compute-budget-and-timeline.md). Dataset details are
sourced in [the bibliography](../09-sources/01-annotated-bibliography.md).
