---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-provisional-leaderboard.md, ../02-prior-art/03-learned-exchange-correlation-functionals.md]
---

# Challenge fit analysis

The Discovered Materials challenge and the NPA idea are close enough in\nmotivation to be confused, and far enough apart in interface to be\nincompatible. This document states the gap precisely, quantifies it, and lays\nout the three routes by which the project could legitimately produce a\nchallenge-shaped artefact — with an honest assessment of what each costs.

**Bottom line**

- A valid submission must be **an exchange–correlation functional**: a\n  density-to-energy map evaluated inside a Kohn–Sham self-consistent field\n  loop, in a production code, timed on one CPU core.
- NPA as proposed is **not a functional**. It does not take a density, does not\n  run inside SCF, and does not output an $E_{xc}$.
- The gap is not conceptual hand-waving: it is three hard requirements —\n  density input, SCF stability, and code integration — none of which the\n  current design addresses.
- Three routes exist: **A** pivot to a learned functional, **B** build an\n  energy surrogate and score the same observables without submitting, **C**\n  extend the particle automaton to grid points. Route B is the project's\n  current plan; Route C is the interesting long shot.
- Route C is more credible than the source note assumed, because Skala already\n  demonstrates that non-local mixing between spatial points is the winning\n  ingredient.

## What the challenge actually requires

From the [challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/)\n(retrieved 2026-11-07), verbatim where possible:

| Requirement | Detail |
|---|---|
| **Deliverable** | \"A more accurate exchange–correlation functional that improves DFT predictions without sacrificing computational efficiency\" |
| **Scored on** | Reaction energies, activation barriers, binding energies, bond dissociation energies for ALD/CVD precursor chemistry |
| **Hidden benchmark** | Reference-quality values not disclosed to entrants |
| **Public validation** | GMTKN55 |
| **Metrics** | Accuracy (target <1 kcal/mol), compute time per molecule, reproducibility |
| **Timing protocol** | def2-QZVP, single CPU core, median of 3 runs; also A100 |
| **Target** | Under 1 kcal/mol |

Three implications that are easy to miss:

1. **The functional must be usable in a real SCF loop.** A model that requires
   a special workflow, a pretrained embedding, or non-standard inputs is not
   deployable, regardless of accuracy.
2. **Timing is measured on the functional's marginal cost**, not on training or
   data generation. The evaluation is inference-only.
3. **Reproducibility is a scored axis.** A model whose results depend on a
   specific GPU, library version, or random seed fails this axis.

> **In plain words.** The competition wants a drop-in replacement part for an\n> existing engine, tested on a hidden exam, and it must be fast and repeatable.\n> It does not want a new kind of engine, however clever.

## Where the NPA idea sits

| Requirement | NPA as designed | Gap |
|---|---|---|
| Input is electron density | Input is particle positions + features | **Fundamental** |
| Output is $E_{xc}$ per point | Output is state/position increments | **Fundamental** |
| Runs inside SCF | Runs as a standalone simulator | **Fundamental** |
| Evaluated per molecule on CPU | Designed for GPU particle systems | Large engineering |
| Stable under self-consistency | No SCF loop exists | Untested |
| Reproducible bitwise | GPU atomics, stochastic mask | Moderate |
| Beats ωB97M-V on barriers | No barrier output at all | **Fundamental** |

Four of seven rows are fundamental. That is not a tuning gap; it is a different\ntype of object. The source note says this clearly, and the project's charter\nrecords it as [ADR 0002](../adr/0002-research-first-not-submission.md).

> **In plain words.** Four of the seven requirements cannot be met by improving\n> the current design. They would require building a different thing.

## Route A — Pivot to a learned functional

**What it is.** Abandon the particle automaton and build a Skala-like learned\nfunctional: density features on a grid, a local network, a non-local mixing\nmodule, trained on high-accuracy energy differences inside an SCF loop.

**What it would take.**

| Requirement | Effort | Feasibility for a small team |
|---|---|---|
| CCSD(T)/CBS training data at ~10⁵ scale | Multi-year, or a collaboration | **Blocking** |
| PySCF integration | Months | Feasible |
| SCF-stable training protocol | Months of research | Hard |
| Benchmark evaluation | Weeks | Feasible |
| Compute for training | Tens of thousands of GPU-hours | Expensive |

**Verdict.** The blocking item is data. Skala's moat is MSR-ACC — ~400,000\nCCSD(T)/CBS-quality energy differences assembled by experts over years. There\nis no public equivalent. A small team cannot bootstrap this, and training on\nωB97M-V labels caps the result below the current state of the art.

**When it becomes viable.** If MSR-ACC or an equivalent is released, or if a\ncollaboration supplies labels. Then Route A is the highest-credibility path,\nbecause it answers the question directly.

> **In plain words.** This route needs a dataset that does not exist publicly.\n> Without it, you are trying to win a cooking contest without ingredients.

## Route B — Energy surrogate, scored on the same observables

**What it is.** Build the energy-based hybrid (Variant 3), evaluate it on\nbarrier heights and reaction energies from the same reference chemistry, and\nreport the numbers next to the leaderboard — without submitting.

**What it proves.** That a fast surrogate can match or beat a functional on the\nobservables the challenge cares about, at lower cost. That is a legitimate\nscientific claim even though it is not a submission.

**What it does not prove.** That the model can be used as a functional. It\ncannot, and claiming otherwise would be rejected immediately by any referee\nwho knows the difference.

**Cost.** This is the project's current plan (phases 0–4). It is achievable\nwith public data and one to four GPUs.

**Evaluation design.** Match the challenge's protocol where possible:

- Use def2-QZVP single-point references at the same geometries.
- Report barrier MAE on a held-out reaction family.
- Time inference per molecule on one CPU core, and separately on one GPU.
- Report reproducibility: seeds, versions, container.

**Honest framing.** \"A machine-learned dynamics surrogate achieves X kcal/mol\nbarrier MAE at Y seconds per molecule, versus ωB97M-V at 3.81 kcal/mol and\n43.5 s, and is not a drop-in functional.\" That sentence is defensible and\ninteresting. \"We beat the challenge\" is not.

> **In plain words.** We can run the same race and post our time, without\n> claiming we entered the same event.

## Route C — Particle automaton on grid points

**What it is.** Take the NPA machinery — local perception, shared rule,\niterated application, persistent state — and apply it to the integration grid\nof a DFT calculation, producing an enhancement factor that is integrated to\ngive $E_{xc}$.

**Why it is more credible than it looks.** Skala's architecture already does\nthe essential thing: each grid point exchanges information with an atom-centred\ncoarse point, and removing that exchange roughly doubles the error. The winning\ningredient is *learned non-local communication between spatial points*. NPA is\na general framework for exactly that.

**Why it is still hard.**

| Obstacle | Detail |
|---|---|
| **Density features, not particles** | Grid points do not move; the \"particle\" abstraction must be reinterpreted as a fixed graph with learned messages |
| **SCF stability** | The functional's derivatives must be smooth enough for self-consistency; a learned message-passing layer is not obviously smooth |
| **Cost target** | Skala achieves semi-local asymptotic cost by keeping the non-local branch small; a full NPA would blow the budget |
| **Integration** | Needs a modifiable DFT code (PySCF is the realistic choice) |
| **Data** | Same blocking issue as Route A |

**The tractable sub-question.** Do not try to build the whole functional. Ask:\n*at equal parameter count and equal asymptotic cost, does a different mixing\ntopology — k-nearest-neighbour graph, persistent state, higher body order —\nimprove on Skala's coarse-point scheme?* That can be tested on a small dataset\nwith a small model, and it is a genuine contribution either way.

**Verdict.** Route C is a phase-5 experiment conditional on a collaborator with\nDFT integration experience and access to high-quality labels. It is not a\nstarting point.

> **In plain words.** The idea of applying the automaton to grid points is\n> sound — the best existing method already does a simplified version. But\n> building the whole thing requires the same missing dataset as Route A, plus a\n> quantum chemistry code you can modify.

## Gap analysis, quantified

If the project wanted to submit today, here is the distance:

| Milestone | Current state | Needed | Estimate |
|---|---|---|---|
| Density input | none | density + gradient + kinetic energy density features | 2 weeks |
| Grid-point graph | none | neighbour construction over integration grid | 3 weeks |
| SCF-compatible output | none | enhancement factor with bounded derivatives | 1 month |
| SCF convergence | untested | stable on GMTKN55 | 2–6 months |
| Training data | none | ~10⁵ CCSD(T)/CBS energy differences | **blocking** |
| PySCF integration | none | working functional interface | 2 months |
| Benchmark | none | full GMTKN55 + timing | 1 month |
| **Total** | | | **not achievable without data** |

The data row is the one that cannot be compressed by effort.

## What would need to be true

For Route C to become the main line rather than a side experiment:

1. High-accuracy training data becomes available at ~10⁵ scale.
2. A collaborator owns a DFT code integration.
3. The SCF stability problem turns out to be tractable with smooth activations
   and bounded outputs.
4. The non-local module can be kept small enough to preserve the cost argument.

Any one of these being false does not kill the route, but all four being true\nis required for it to be worth a year.

> **In plain words.** Four things have to line up. Three are engineering; one\n> is a dataset that does not exist. Bet accordingly.

## Recommendation

1. **Proceed with Route B** as the primary project. It is achievable, it
   produces a real scientific result, and it can be evaluated against the
   challenge's numbers without pretending to be a submission.
2. **Keep Route C as a written hypothesis**, with the tractable sub-question
   defined, so that it can be picked up if a collaborator or dataset appears.
3. **Do not start Route A.** Without MSR-ACC-scale data it is a guaranteed
   negative result with a high cost.
4. **State the non-submission explicitly** in any public write-up. Reviewers
   forgive scope; they do not forgive misrepresentation.

## Open questions

- Would the challenge organisers accept an energy surrogate evaluated on their
  hidden benchmark, as an unscored demonstration? Worth asking; the answer
  would strengthen Route B considerably.
- Is PySCF's functional interface flexible enough to accept a message-passing
  module without patching the SCF loop? Needs a spike.
- Does Skala's coarse-point scheme have a published ablation on *topology*
  (e.g. k-NN vs atom-centred)? If not, that is a clean, small contribution.

## What would change this document

- Release of MSR-ACC or equivalent, which would make Route A viable.
- A challenge rule change admitting surrogate models, which would make Route B
  a submission.
- A publication showing that learned non-local mixing can be made SCF-stable
  at semi-local cost, which would de-risk Route C substantially.

## Sources

1. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry*. <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07).
2. Luise et al., *Skala*, arXiv:2506.14665v6, §2.2 and §3.1.
   <https://arxiv.org/abs/2506.14665> (retrieved 2026-11-07).
3. Kim et al., *Neural Particle Automata*, arXiv:2601.16096.
   <https://arxiv.org/abs/2601.16096> (retrieved 2026-11-07).
4. Levine et al., *OMol25*, arXiv:2505.08762.
   <https://arxiv.org/abs/2505.08762> (retrieved 2026-11-07).
