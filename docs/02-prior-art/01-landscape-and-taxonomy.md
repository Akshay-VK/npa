---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [../00-orientation/03-critical-assessment-of-the-idea-note.md]
---

# Landscape and taxonomy

There are four distinct ways to attack the speed–accuracy problem in
computational chemistry, plus a fifth that is not machine learning at all.
They are routinely confused in conversation because they all produce "a number
for a molecule". They are not interchangeable. This document draws the map so
that the project can say precisely which square it occupies, and so that any
claim of novelty can be checked against the right neighbours.

**Bottom line**

- The field has four families: better functionals, learned functionals, learned
  potentials, and learned dynamics surrogates. They differ in *interface* — what
  you feed in and what you get out — more than in algorithm.
- The Discovered Materials challenge asks for family 2. NPA is family 4. The gap
  is structural, not a matter of tuning.
- Family 3 is where almost all the money, data, and talent currently sits. Any
  claim of competitiveness must be measured against it.
- Family 1 sets the accuracy ceiling that family 2 is trying to break, and the
  baselines that family 4 must beat.
- The most defensible niche for this project is a *cost-targeted* member of
  family 4 with an energy interface, which is a hybrid of 3 and 4.

## The four families

### Family 1 — Hand-designed density functionals

**Interface:** electron density (and its gradients, kinetic energy density,
orbitals) → exchange–correlation energy.

**What it is:** the traditional approach. LDA → GGA → meta-GGA → hybrid →
double hybrid → RPA. Each rung adds an ingredient and cost. This is what the
challenge calls "DFT" and what most practitioners mean by it.

**What it is good at:** speed, interpretability, and being the default in every
quantum chemistry code. A GGA calculation is seconds per molecule.

**What it cannot do:** reach chemical accuracy for reaction barriers across
diverse chemistry. The best functional on the provisional leaderboard,
ωB97M-V, is at 3.81 kcal/mol WTMAD-2, roughly four times the 1 kcal/mol target
([challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/),
retrieved 2026-11-07).

See [the functional zoo](02-functional-zoo-and-jacobs-ladder.md).

> **In plain words.** These are hand-written recipes for how electrons push on
> each other. People have spent fifty years improving the recipes. They are
> fast and decent, but nobody can write a recipe that is exactly right, because
> the exact answer is not expressible as a simple formula.

### Family 2 — Learned density functionals

**Interface:** same as family 1 — density in, energy out — but the functional
is a neural network trained on high-accuracy data.

**What it is:** DM21 (DeepMind, 2021), Skala (Microsoft, 2025–2026), and
related work. These replace the hand-designed *form* of the functional with a
learned one, while keeping the Kohn–Sham machinery intact.

**What it is good at:** the best published learned functional, Skala, reports
2.8 kcal/mol WTMAD-2 on GMTKN55 "while retaining the lower computational cost
characteristic of semi-local DFT"
([arXiv:2506.14665](https://arxiv.org/abs/2506.14665)). That is a genuine
improvement on ωB97M-V at far lower cost.

**What it cannot do (yet):** generalise robustly outside its training
distribution, run cheaply enough for every code, and avoid the failure modes
documented for DM21 — poor extrapolation to transition metals and a cost higher
than global hybrid DFT in practice. See
[learned exchange–correlation](03-learned-exchange-correlation-functionals.md).

> **In plain words.** Same input and output as the hand-written recipes, but
> the recipe is learned from data instead of designed by a chemist. It is the
> most direct answer to the competition's question, and it is where the
> strongest existing result lives.

### Family 3 — Learned interatomic potentials

**Interface:** nuclear positions and element identities → energy, and forces by
differentiation.

**What it is:** the MLIP family. Behler–Parrinello, SchNet, NequIP, MACE,
Allegro, ANI, and the universal models (UMA, MACE-MP, Orb, eSEN). The model
replaces the *entire electronic structure calculation* for a given
configuration, not a component of it.

**What it is good at:** accuracy at 10³–10⁶× the speed of DFT, with forces
accurate enough to run dynamics. This is the technology that made
million-atom MD feasible.

**What it cannot do (by default):** reactions. Trained on near-equilibrium
configurations, these models have never seen a bond break and produce
confident nonsense when one does. Reactive variants exist and are family 3.5 —
see [reactive potentials](07-reactive-potentials-and-enhanced-sampling-models.md).

**Scale of the field:** OMol25 alone contains more than 100 million DFT
calculations at ωB97M-V/def2-TZVPD, across 83 elements and systems up to 350
atoms ([arXiv:2505.08762](https://arxiv.org/abs/2505.08762)). UMA is trained on
it plus other datasets. This is not a niche.

See [MLIPs](05-machine-learned-interatomic-potentials.md) and
[universal potentials](06-universal-potentials-and-foundation-models.md).

> **In plain words.** Instead of improving the theory of electrons, skip it:
> learn directly from millions of examples what the energy is for a given
> arrangement of atoms. This works spectacularly well for normal molecules and
> badly for reactions, because the training data contains almost no reactions.

### Family 4 — Learned dynamics surrogates

**Interface:** a state (positions, velocities, maybe latent variables) → the
next state, or the derivative of the state.

**What it is:** models that learn the *evolution*, not just the energy. NPA is
here. So are neural operators for PDEs, GNN rollout models, learned
coarse-grained dynamics, and generative trajectory models.

**What it is good at:** speed, and the ability to model phenomena where the
energy is not the natural object (dissipative systems, coarse-grained dynamics,
non-conservative processes).

**What it cannot do (yet):** guarantee conservation, provide barriers, or
generalise beyond the training distribution. A direct-update model has no
energy, so it cannot report a reaction energy or a barrier at all. Error
compounds multiplicatively over a rollout in a way single-point models never
experience.

**NPA's specific position:** a family-4 architecture with an unusually strong
locality and parameter-efficiency story — the paper reports networks with as
few as ten thousand parameters for 2D morphogenesis
([arXiv:2601.16096](https://arxiv.org/abs/2601.16096)) — but with no energy,
no forces, and no rotational equivariance by construction. Moving it to
family 3.5 (energy-based hybrid) is the project's central architectural bet.

See [NCA lineage](08-neural-cellular-automata-lineage.md) and
[architecture space](../03-method-design/01-architecture-space.md).

> **In plain words.** Instead of learning the landscape, learn the walk. This
> is what the graphics model does: it learns how particles move, not what
> energy they have. It is fast and flexible, but it cannot tell you how high a
> hill is, only how particles tend to travel.

### Family 5 — Classical acceleration (the non-ML control group)

**Interface:** varies.

**What it is:** semi-empirical methods (PM6, GFN2-xTB), tight-binding (DFTB),
QM/MM, implicit solvation, and classical force fields. These are the incumbent
fast methods. They are routinely omitted from ML papers' comparisons, which is
a mistake: a model that is slower than GFN2-xTB and less accurate than PBE0 has
no reason to exist.

**Why it matters here:** the challenge measures compute time per molecule on a
single CPU core. xTB and DFTB are the natural speed references. Any "we are
fast" claim must be positioned against them, not only against DFT.

> **In plain words.** There were fast, approximate methods before machine
> learning, and they are still good. If a new model is slower and less accurate
> than one of them, it is a hobby, not a tool.

## The map

| | Family 1<br>Functionals | Family 2<br>Learned XC | Family 3<br>MLIPs | Family 4<br>Dynamics | Family 5<br>Classical |
|---|---|---|---|---|---|
| **Input** | electron density | electron density | atomic structure | state + time | varies |
| **Output** | $E_{xc}$ | $E_{xc}$ | $E$, $\mathbf{F}$ | next state | $E$, $\mathbf{F}$ |
| **Runs inside DFT?** | yes | yes | no | no | no |
| **Gives barriers?** | yes | yes | yes | only if energy-based | yes |
| **Conserves energy?** | by construction | by construction | yes (if energy-based) | rarely | yes |
| **Typical cost** | seconds/molecule | seconds/molecule | ms/molecule | µs–ms/step | ms/molecule |
| **Maturity** | very high | research | high, exploding | low | very high |
| **Challenge-eligible?** | yes (baseline) | **yes (target)** | no | no | no |
| **This project** | baseline | adjacent | main rival | **home** | must beat |

> **In plain words.** The table is the whole document in one glance. Read the
> "input" and "output" rows: those define the family, not the algorithm. Two
> models with the same architecture but different inputs are in different
> families and cannot be compared directly.

## Where the money and the data are

A crude but useful signal: count the public datasets and pretrained models.

- Family 2 has **GMTKN55** (55 subsets, CCSD(T) references) and a handful of
  learned functionals with released weights. Small, high-value data.
- Family 3 has **OMol25** (100M+ points), **OMat24** (110M), **Transition1x**
  (9.6M), **SPICE**, **MD17**, **ANI-1x**, and dozens of pretrained models.
  Enormous, well-funded.
- Family 4 has almost nothing public. There is no standard reactive-trajectory
  benchmark at scale. This is simultaneously the opportunity and the warning:
  no data means no competition, and also no validation.

*(inference)* The absence of a family-4 benchmark is why the NPA-for-chemistry
idea is under-explored, and why a serious contribution would include building
the benchmark, not just the model.

> **In plain words.** Everyone is building potentials because the data is
> there. Almost nobody is building dynamics models because the data is not.
> That is either an opening or a warning sign, and probably both.

## The strategic reading

Three observations follow from the map, and they drive the project's strategy.

**1. The challenge and the idea live in different families.** The challenge
asks for family 2. The idea is family 4. A family-4 model can be *scored* on
the same observables and can be a useful scientific result, but it cannot be
submitted. This is settled and recorded in
[ADR 0002](../adr/0002-research-first-not-submission.md).

**2. Family 3 is the real competition, not family 1.** A reviewer will not ask
"is this better than PBE?" They will ask "is this better than MACE, and is it
faster than UMA?" The baselines must be drawn from family 3.

**3. The only defensible novelty is the intersection.** Family 3 has no
persistent state. Family 4 has no energy. The intersection — persistent latent
state inside a conservative potential — is thin, unexplored, and genuinely
novel. That is the whole bet.

> **In plain words.** We are not competing with the best existing thing
> head-on. We are trying a combination nobody has tried: the memory of a
> graphics automaton plus the physics of a potential. If that combination does
> not help, the project has no reason to exist, and we should find that out
> fast.

## What this project is *not* competing with

Naming these prevents wasted effort:

- **Not competing with UMA on breadth.** 83 elements, 350 atoms, trained on
  billions of core-hours. A small team cannot match coverage.
- **Not competing with Skala on functional accuracy.** That requires
  wavefunction-level training data at scale.
- **Not competing with xTB on raw speed.** A well-optimised semi-empirical
  method is microseconds per atom.
- **Not competing on generality.** The project targets one chemistry well.

The only axis where a small team can win is **the accuracy–cost frontier for
reactive dynamics in a narrow domain**, and even there only if persistent state
does real work.

> **In plain words.** Do not pick a fight you cannot win. Breadth, raw speed,
> and general coverage are lost causes. One narrow thing done better is the
> only realistic goal.

## Open questions

- Is there an existing family-4 model for chemistry that has been benchmarked
  properly? The literature search suggests not, but this needs a systematic
  check before claiming novelty.
- Does any MLIP use persistent state across steps? Within-call features are
  standard; cross-step memory appears absent, but confirm.
- Where do neural operators for molecular dynamics sit? They are family 4 but
  operate on densities or fields rather than particles.

## What would change this document

- A published energy-based particle automaton for chemistry, which would move
  the project from novel to replication.
- A family-4 benchmark suite appearing, which would change the data strategy
  from "build it" to "use it".
- Evidence that family 2 has effectively solved reaction barriers, which would
  make family 4 irrelevant to the challenge framing.

## Sources

1. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry*. <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07).
2. Luise et al., *Accurate and scalable exchange–correlation with deep
   learning* (Skala), arXiv:2506.14665.
   <https://arxiv.org/abs/2506.14665> (retrieved 2026-11-07).
3. Levine et al., *The Open Molecules 2025 (OMol25) Dataset, Evaluations, and
   Models*, arXiv:2505.08762. <https://arxiv.org/abs/2505.08762> (retrieved
   2026-11-07).
4. Kim et al., *Neural Particle Automata*, SIGGRAPH 2026, arXiv:2601.16096.
   <https://arxiv.org/abs/2601.16096> (retrieved 2026-11-07).
5. Schreiner et al., *Transition1x*, Scientific Data 9, 2022.
   <https://www.nature.com/articles/s41597-022-01870-w> (retrieved 2026-11-07).
