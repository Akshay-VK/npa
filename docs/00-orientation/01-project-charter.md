---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: []
---

# Project charter

This project asks one question: **can a small, local, shared learned rule with
persistent per-particle state predict chemical reaction dynamics better, per
unit of compute, than the methods that already exist?** Everything else in
`docs/` exists to make that question answerable, and to make the answer
survive contact with someone who does not believe it.

**Bottom line**

- The primary deliverable is a *research result*, not a challenge submission.
  The challenge asks for an exchange–correlation functional; the idea in the
  source note is a dynamics surrogate. Those are different objects and the
  gap cannot be papered over (see [challenge fit](../06-leaderboard/02-challenge-fit-analysis.md)).
- The distinctive claim worth testing is *persistent latent state on top of a
  conservative energy model*, not "NPA applied to molecules". If plain local
  models match it, the project has failed informatively and cheaply.
- Phase 2 — a two-species toy world with a known potential — is the decision
  point. It costs days, not months, and it can kill the architecture.
- Every phase ships a versioned artefact (code, config, data manifest,
  results) so that iteration 2 does not silently inherit iteration 1's bugs.
- Credibility comes from honest baselines. A result that beats a strawman is
  worth nothing; a result that ties UMA on one narrow task and is 100× faster
  is worth a paper.

## What this project is

A multi-iteration research programme with four outputs:

1. **A testable architecture family.** A formal specification of an
   atomistic neural particle automaton, with the design axes separated so
   that each can be ablated (see [architecture space](../03-method-design/01-architecture-space.md)).
2. **A runnable implementation.** Small enough to train on one GPU, fast
   enough to iterate weekly, instrumented enough to diagnose failure.
3. **An evaluation harness.** Fixed splits, fixed metrics, fixed baselines,
   so that version 2 can be compared to version 1 without re-litigating the
   protocol.
4. **A written record.** These documents, a paper draft, and a public
   write-up aimed at people who will try to reproduce or refute the result.

## What this project is not

- **Not a new exchange–correlation functional.** A functional maps electron
  density to energy inside a Kohn–Sham self-consistent field loop. A dynamics
  surrogate maps nuclear configuration to energy and forces. Confusing them
  is the single most common category error in this space, and the source note
  is right to flag it. The speculative grid-particle extension in
  [challenge fit](../06-leaderboard/02-challenge-fit-analysis.md) is the only
  bridge, and it is explicitly a later-stage hypothesis.
- **Not a universal potential.** The target domain is small-molecule
  main-group reaction chemistry, initially H/C/N/O. Claiming more without
  evidence is how this field generates retractions.
- **Not a replacement for DFT.** The model will be trained on DFT labels and
  therefore inherits DFT's errors. Beating DFT requires higher-fidelity
  labels, which is a data problem (see [label fidelity](../04-data/03-label-fidelity-and-multifidelity.md)).
- **Not a graphics project.** The NPA machinery is borrowed; the success
  criteria are physical, not visual.

> **In plain words.** Think of this as building a very fast, very small
> calculator that watches atoms move and learns to predict what they do next.
> It is not trying to reinvent the theory of electrons, and it is not trying
> to be right about every molecule in the universe. It is trying to be right
> about a narrow, important class of chemical reactions, and to be honest
> about where it stops being right.

## Goals, in priority order

| Priority | Goal | Why it is ranked here |
|---|---|---|
| 1 | Establish whether persistent latent state buys anything over a strong local baseline | This is the only claim that is unique to the idea. Everything else is re-implementation. |
| 2 | Build a conservative, stable, physically plausible dynamics model | Without this, trajectory results are unfalsifiable animations. |
| 3 | Quantify the accuracy–cost frontier against real baselines (UMA, MACE, DFT) | The pitch is a trade-off; a single accuracy number cannot support it. |
| 4 | Produce a reproducible artefact set and a defensible write-up | An unreproducible result is a rumour. |
| 5 | Optionally, map the result onto the Discovered Materials challenge format | Valuable, but derivative. Do not let it distort goals 1–4. |

### Why goal 5 is last

The challenge's stated task is "develop a more accurate exchange–correlation
functional that improves DFT predictions without sacrificing computational
efficiency" ([challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/),
retrieved 2026-11-07). A functional is a component *inside* DFT. A dynamics
surrogate replaces the whole DFT-plus-integrator stack. A surrogate can be
scored on the same *observables* (barriers, reaction energies) but cannot be
submitted as a functional. Treating the challenge as a yardstick rather than a
target is a deliberate decision, recorded in
[ADR 0002](../adr/0002-research-first-not-submission.md).

> **In plain words.** The competition is asking for a better engine part.
> We are building a different kind of vehicle. We can still race on the same
> track and compare lap times, but we cannot enter our vehicle as an engine.
> Pretending otherwise would waste the whole project.

## Success criteria

Criteria are written so that a negative result still counts as success. A
project that answers "no, and here is the evidence" has done its job.

| Phase | Question | Pass condition | Kill condition |
|---|---|---|---|
| 0 | Is the literature and tooling understood? | These docs reviewed; NPA code runs | Cannot reproduce the NPA demo |
| 1 | Does the toolchain work end to end? | Toy system trains, rolls out, and conserves energy to a stated tolerance | Cannot close the loop on synthetic data |
| 2 | Does persistent state help? | Hybrid beats a matched no-state baseline on rollout error at equal parameter count and equal compute, with non-overlapping confidence intervals | No measurable benefit on two independent toy potentials |
| 3 | Does it survive a real reaction? | H + H₂ barrier within a stated tolerance; correct qualitative barrier location | Cannot find the barrier at all |
| 4 | Does it scale to organic chemistry? | Competitive with a pretrained baseline on a held-out Transition1x subset, at lower cost | Worse on both axes with no compensating advantage |
| 5 | Is there a story? | Paper draft or challenge-format result | Neither |

Numbers in the "pass condition" column are deliberately not fixed yet. They
must be set *before* running the experiment, from a power analysis, not after
looking at the result. See
[metrics and statistics](../05-evaluation/02-metrics-and-statistics.md).

> **In plain words.** A fair test is one where you write down in advance what
> would prove you wrong. If you only decide what counts as success after you
> see the numbers, you will always succeed, and you will always be wrong.

## Operating principles

1. **Cheapest experiment first.** If a claim can be tested in two dimensions
   with a Lennard-Jones potential, do not test it with DFT.
2. **One variable per iteration.** Version numbers change one design axis at
   a time. Otherwise the result is unattributable.
3. **Baselines are not optional.** Every result ships with the strongest
   cheap baseline, the strongest expensive baseline, and a null model.
4. **Physical invariants are tests, not decorations.** Energy drift,
   momentum conservation, and rotational consistency are automated checks.
5. **Write the failure down.** A negative result that is documented saves the
   next person a month.

> **In plain words.** Do the cheap test before the expensive one, change one
> thing at a time, and always compare against something real. Most research
> time is lost by skipping these three habits, not by lacking ideas.

## Scope boundaries

**In scope, initially**

- Neutral and charged small molecules containing H, C, N, O.
- Gas-phase and cluster chemistry, single electronic state, no explicit
  solvent.
- Fixed temperature ensembles with a thermostat, not free-energy
  calculations.
- Barrier heights, reaction energies, and short reactive trajectories.

**Explicitly out of scope until phase 5**

- Transition-metal chemistry (different correlation regime, much harder).
- Periodic solids and surfaces (different boundary conditions, different
  physics).
- Photochemistry and non-adiabatic dynamics (multiple electronic states,
  a separate research programme).
- Free energies and solvation (requires sampling, not just a potential).
- Anything requiring better-than-DFT accuracy without better-than-DFT labels.

Every scope exclusion is a risk if the eventual goal is the ALD/CVD
benchmark, which is explicitly precursor chemistry and may include metals
such as Al and Ti. This tension is recorded in the
[risk register](../08-risk/01-risk-register.md) as R-07.

> **In plain words.** We are deliberately starting with the simplest chemistry
> that still counts as chemistry. That is not a limitation of ambition; it is
> how you find out whether the idea works before spending a year on the hard
> cases.

## Decision rights and review cadence

- **Weekly:** review the experiment log; confirm the next single variable.
- **Per phase:** a written go/no-go against the table above, filed in
  `docs/07-delivery/`.
- **On any change to the core architecture:** an ADR. If it is not worth an
  ADR, it is not worth changing.
- **On any benchmark number entering a public document:** a verification log
  entry with the source, protocol, and retrieval date.

> **In plain words.** Decisions get written down, dated, and reviewed. Not
> because paperwork is fun, but because in six months nobody will remember
> why the model has three heads instead of two.

## Open questions

- Who is the intended reader of the final artefact: a reviewer, a
  practitioner, or a general technical audience? The answer changes how much
  of the physics must be explained.
- Is there a compute budget that makes phase 4 realistic, or is phase 4
  contingent on a grant or a collaborator? See
  [compute budget](../07-delivery/04-compute-budget-and-timeline.md).
- Does the project need to produce a challenge-format artefact for external
  reasons (funding, visibility), which would promote goal 5?

## What would change this document

- Evidence that a learned functional is tractable for a small team, which
  would make goal 5 primary.
- Evidence that persistent state cannot be trained stably at all, which would
  collapse the project to a comparison study of existing potentials.
- A published result that already answers the phase-2 question, which would
  redirect the project to phase 3 or to a replication study.

## Sources

1. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry* (Problem 03, updated Nov 2026).
   <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07; page and leaderboard payload archived in
   [`09-sources/evidence/`](../09-sources/evidence/retrieval.json)).
2. Kim, Pajouheshgar, Süsstrunk, Jakob, Park, *Neural Particle Automata:
   Learning Self-Organizing Particle Dynamics*, SIGGRAPH 2026,
   arXiv:2601.16096. <https://arxiv.org/abs/2601.16096> (retrieved
   2026-11-07).
3. Pajouheshgar et al., NPA project page.
   <https://selforg-npa.github.io/> (retrieved 2026-11-07).
