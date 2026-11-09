---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-project-charter.md]
---

# Critical assessment of the idea note

The source note is a good piece of thinking: it identifies a real bottleneck,
finds a real architectural analogy, and — unusually — names the ways its own
idea might fail. This document audits it line by line, separates what survives
contact with the primary sources from what does not, and adds the objections
the note does not raise. The goal is not to score points. It is to make sure
the project does not spend six months on a load-bearing assumption that was
wrong in paragraph one.

**Bottom line**

- The note's central architectural judgement — that *what the network
  predicts* matters more than *how elements are encoded* — is correct and
  should be promoted from a section to the organising principle of the project.
- Its rejection of per-element networks is right for the wrong reason. The
  real objection is **pair symmetry and data sparsity**, not force
  antisymmetry, which a shared energy sum fixes automatically.
- Its description of NPA's "multi-species" support is factually wrong. The
  paper composes independently trained models; it has no species mechanism.
  This matters because option (a) has no existing implementation to copy.
- Its biggest unexamined assumption is that NPA's *attractor* behaviour is an
  asset. For chemistry it is probably a liability, and this is the single most
  important thing the note misses.
- The dataset numbers check out, but the level of theory does not get enough
  attention: OMol25 is labelled at ωB97M-V, so training on it caps the model
  at a functional that is itself on the leaderboard at 3.81 kcal/mol.

## Verdict scale used here

| Verdict | Meaning |
|---|---|
| **Holds** | Correct as written; rely on it. |
| **Holds with nuance** | Directionally right, but a sentence would mislead a builder. |
| **Needs correction** | Factually wrong or materially incomplete. Fix before building. |
| **Unresolved** | Cannot be settled by reading; needs an experiment. |
| **Missing** | The note does not consider something that matters. |

> **In plain words.** Some statements in the note are simply true, some are
> true but need a warning label, and some are wrong in a way that would send
> the build in the wrong direction. This document sorts them into those piles.

## What the note gets right

Three judgements are worth protecting from later drift.

**1. The speed–accuracy framing is correct.** DFT is cheap enough to run at
scale and wrong enough to matter for barriers; coupled cluster is right
enough and far too expensive. That is the actual state of the field, not a
simplification ([challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/),
retrieved 2026-11-07; [Skala, arXiv:2506.14665](https://arxiv.org/abs/2506.14665)).

**2. The challenge is narrower than its own framing.** The page says
"develop a more accurate exchange–correlation functional that improves DFT
predictions without sacrificing computational efficiency." A dynamics
surrogate is not that. The note says so plainly, which is the right instinct
and rarer than it should be.

**3. Variant 3 is the interesting one.** Energy-based dynamics plus persistent
latent state is the only variant that is simultaneously (a) physically
conservative, (b) benchmarkable on barriers, and (c) genuinely distinct from
an ordinary machine-learned interatomic potential. The note arrives at this
by elimination and it is the right destination.

> **In plain words.** The note is right about the problem, right about the
> competition not asking for what we are building, and right that the hybrid
> design is the one worth pursuing. Those are the three things that matter
> most, and they are the three things that are easiest to get wrong.

## Correction 1 — "multi-species" is not what it sounds like

The note says the project page "advertises a multi-species demo, which is
worth studying for how species are encoded." That is a reasonable inference
from the word *species*. It is wrong.

The NPA paper describes the demo as follows: "multiple independently trained
NPA 'species' can be composed within the same simulation. Each particle
follows its own learned rule, and as groups move and interpenetrate they
become part of one another's neighborhoods and therefore interact, despite
never being co-trained." The observed outcomes range "from near-independence
to cooperation and disruption"
([§4.4, Figure 14](https://arxiv.org/html/2601.16096v3)).

So there are two rules in one simulation, each with its own parameters. There
is no shared trunk, no element embedding, no pair conditioning, and no
mechanism that guarantees the two rules agree about the interaction between a
particle of type A and a particle of type B. That is precisely the failure mode
the note attributes to option (b) — and the paper demonstrates it rather than
solving it.

**Consequence for the project.** Option (a), "one network with element
identity as a fixed per-atom parameter", has *no reference implementation to
copy*. The note's Phase 1 ("understand how species and state are encoded")
will not find an answer, because there is nothing there to find. Budget for
designing the conditioning mechanism from scratch, and treat the multi-species
demo as evidence for why naive composition fails, not as a template.

> **In plain words.** The demo looks like it has different kinds of particle
> that understand each other. Actually it is two separate brains in one body,
> and the paper's own videos show them sometimes fighting. So we cannot copy
> that design; we have to build the "one brain, many elements" version
> ourselves.

## Correction 2 — the per-element objection is right, for a different reason

The note argues that per-element networks are unsafe because "the forces must
be equal and opposite" and "independently trained networks give no guarantee
of this, so you get inconsistent pair interactions, double counting, and
drift."

The force part is not quite right. If each element network contributes a
scalar energy and the total energy is their sum, then

$$
\mathbf{F}_a = -\frac{\partial}{\partial \mathbf{x}_a} \sum_i E_i,
$$

and Newton's third law follows from the translation invariance of the total
energy, not from how many networks produced it. A per-element decomposition
can be exactly conservative. The prior run of this project already caught
this; it is recorded in [element conditioning](../03-method-design/04-element-conditioning.md).

The real objections are sharper:

**(a) Pair symmetry.** An interaction between elements A and B is computed
once by A's network looking at B, and once by B's network looking at A. Unless
the architecture explicitly symmetrises, $E_{AB} \neq E_{BA}$, and the total
energy depends on which atom you evaluate first. This is a genuine architectural
defect, not a training accident.

**(b) Combinatorial data cost.** If interactions are pair-specific, $N$
elements need $N(N+1)/2$ interaction models, not $N$. The note says "N
networks for N elements"; the honest count is quadratic. For 4 elements that
is 10; for 20 it is 210.

**(c) Non-stationarity.** Training N networks jointly means each network's
gradient depends on the others' current parameters. The note calls this a
"coupled, non-stationary training problem" and that phrase is exactly right.

**What survives.** The note's proposed middle ground — shared trunk with
per-element heads or adapters, or conditioning on the pair $(Z_i, Z_j)$ — is
the standard solution and is correct. The experiment to settle it is cheap and
is specified in [baselines and ablations](../05-evaluation/04-baselines-and-ablations.md).

> **In plain words.** The note says separate networks per element will break
> Newton's third law. They will not, as long as you add up one total energy and
> take derivatives of that. But they will break something worse: the energy of
> an A–B pair will depend on which atom you ask. Fixing that needs symmetry
> built in, and it needs far more data than the note implies.

## Correction 3 — a perception radius is not an interaction cutoff

The mapping table equates "SPH neighbourhood and support radius" with
"interaction cutoff", with the comment that bonding is short-range but
electrostatics and dispersion are not.

The comment is true. The mapping is not. In an SPH perception operator, the
support radius $\epsilon$ is a *smoothing scale*: it controls how much
neighbourhood is averaged into a feature. Change $\epsilon$ and you change the
representation, but you do not change the physics. In an interatomic potential,
the cutoff $r_c$ is a *physical truncation*: pairs beyond it contribute
exactly zero energy, and the choice of $r_c$ changes the answer.

These are different knobs with different failure modes. A large $\epsilon$
gives smoother, more robust features and blurs local chemistry. A large $r_c$
gives more accurate long-range physics and costs more. Conflating them leads
to a model that appears to have a cutoff but does not, or one that claims
long-range physics it cannot represent.

**Consequence.** The architecture needs *two* radii, declared separately: a
perception radius for the neural features, and an energy cutoff (plus explicit
long-range terms) for the physics. See
[long-range interactions and charge](../03-method-design/06-long-range-interactions-and-charge.md).

> **In plain words.** One dial controls how blurry the model's eyes are. A
> different dial controls how far the physics reaches. The note treats them as
> the same dial, which would make it impossible to tell whether a change made
> the model see better or reach further.

## Correction 4 — the dataset ceiling is not "DFT", it is a specific functional

The note says "training on DFT labels means the model cannot beat DFT", which
is true but too coarse. The relevant statement is more damaging.

OMol25, the largest available molecular dataset, contains more than 100
million DFT calculations **at the ωB97M-V/def2-TZVPD level of theory**, covering
83 elements, systems up to 350 atoms, and roughly 83 million unique systems
([OMol25, arXiv:2505.08762](https://arxiv.org/abs/2505.08762)). ωB97M-V is the
best functional on the challenge's provisional leaderboard, at 3.81 kcal/mol
WTMAD-2 ([challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/)).

So the ceiling is not "DFT" in the abstract. It is **a specific, already
near-best functional**. A model trained only on OMol25 cannot credibly claim
to beat ωB97M-V; it can at best reproduce it more cheaply. Any claim of
*better* accuracy requires labels from a higher rung: CCSD(T)-quality data
(Transition1x, GMTKN55's reference values) or a multi-fidelity correction.

The note does say this in its accuracy-ceiling bullet and its multi-fidelity
suggestion. What it does not do is connect the two facts: the largest dataset
is labelled by the second-best method on the leaderboard, so **the data
landscape is actively adversarial to the accuracy goal**. That should be
stated as a primary risk, not a footnote.

> **In plain words.** The biggest, most convenient pile of training data was
> labelled by a method that is already almost the best on the scoreboard. If
> we learn only from that pile, the best we can do is imitate the runner-up.
> To actually win, we need a smaller, much more expensive pile of better
> labels.

## The missing objection — NPA learns attractors, chemistry is not an attractor

This is the most important thing in this document.

Every NPA task in the paper is a **target-state problem**. Morphogenesis: any
trajectory that ends in the right shape is correct. Texture synthesis: any
arrangement that matches the target statistics is correct. Point-cloud
classification: any dynamics that reach consensus are correct. The loss is
computed on the *rendered endpoint* (or on the final consensus vector), not on
the path.

That is why robustness and regeneration are presented as headline features.
A model trained this way is explicitly pushed toward a stable attractor: perturb
it, and it returns. The paper even observes persistent internal flows after the
target is reached, and speculates that they act as "distributed memory" that
maintains the morphology.

Chemistry is the opposite problem. A reaction is a *departure* from an
attractor. The reactant basin is a stable attractor; the whole point of the
simulation is to leave it, cross a barrier, and fall into a different basin.
A model optimised for self-repair will do exactly the wrong thing: it will
pull a trajectory back toward the reactant geometry, damping the very
fluctuation that should have become a reaction.

This is not a small implementation detail. It changes:

- **The training objective.** You must supervise per-frame forces and energies,
  not endpoints. A trajectory loss alone will teach the model to stay put.
- **The evaluation.** Regeneration under perturbation is not a virtue here; it
  is a red flag. The test is whether the model preserves the *barrier*, not
  whether it recovers a shape.
- **The architecture's selling point.** "Robust, self-healing dynamics" is a
  liability in a dynamics surrogate. The project should stop repeating that
  framing.
- **The stochastic update mask.** NPA's Bernoulli mask is a regulariser that
  encourages asynchronous convergence. In chemistry it is a source of
  non-physical noise unless it is mapped onto a real stochastic process
  (Langevin) with a defined temperature.

The note gets close to this in §3 ("every task so far is a target-shape
problem, not a match-a-physical-trajectory problem") and then does not follow
the thought through. It is the difference between a system that is trained to
*arrive* and a system that is trained to *obey*.

**Recommendation.** Make this the first thing the toy-world experiment tests.
Train the same architecture with (i) an endpoint/attractor loss and (ii) a
force-matching loss, on the same data, and measure whether the attractor-trained
model suppresses barrier crossings. If it does — and it should — the project
has a clean, publishable negative result about transferring NCA intuitions to
dynamics, and a clear reason to adopt the energy-based variant.

> **In plain words.** The graphics model is trained to end up in the right
> shape, and it is proud that it repairs itself if you break it. A chemical
> reaction is the opposite: the molecule has to *stop* repairing itself and
> fall apart in a specific way. A self-healing model is a model that refuses
> to react. This is the biggest thing the note missed, and it is testable in
> a week.

## The unstated axis — what is the observable?

The note compares variants by what they can output (positions, energy, both).
It does not ask what the *user* needs. Three different observables imply three
different models and three different benchmarks:

| Observable | What must be right | Benchmark | Hardest part |
|---|---|---|---|
| **Single-point energy** | The PES at a configuration | Reaction energies, binding energies | Absolute accuracy, cancellation |
| **Barrier height** | The PES along a path, especially the saddle | Barrier MAE vs CCSD(T) | Saddle-point regions, rarely sampled |
| **Rate constant** | Barrier *and* prefactor *and* recrossing | Experimental kinetics | Entropy, tunnelling, dynamics |
| **Trajectory** | Forces everywhere along the path | RMSD, stability, event statistics | Error accumulation, rare events |

A model can be excellent at the first and useless at the third. The note's
evaluation section lists these as parallel metrics rather than a hierarchy.
They are a hierarchy: trajectory accuracy implies single-point accuracy, not
the reverse. Decide which one the project is selling before designing the
loss. See [evaluation design](../05-evaluation/01-evaluation-design.md).

> **In plain words.** "Accurate" can mean four different things: right energy,
> right hill height, right reaction speed, or right movie. They are not
> interchangeable, and being good at one does not make you good at the others.
> Pick the one you are actually promising.

## Section-by-section verdicts

| § | Claim | Verdict | Action |
|---|---|---|---|
| 1 | NPA is a particle generalisation of NCA; point it at chemistry | Holds | Proceed |
| 1 | Two ways to encode elements; extra conditioning needed | Holds with nuance | Conditioning is a smaller lever than the prediction target |
| 1 | Speed–accuracy barrier motivates the work | Holds | Proceed |
| 2 | Challenge asks for an XC functional, not a surrogate | Holds | Record in ADR 0002 |
| 2 | Leaderboard numbers and target <1 kcal/mol | Holds | Verified; see [leaderboard](../06-leaderboard/01-provisional-leaderboard.md) |
| 3 | NPA tasks, 10k parameters, SPH perception | Holds | Verified against paper |
| 3 | Multi-species demo shows how species are encoded | **Needs correction** | Independent models, no species mechanism |
| 3 | No energy/forces/conservation in NPA | Holds | Central design constraint |
| 3 | Rotation equivariance unclear | Holds — and worse than stated | Paper says it is *not* enforced |
| 4 | SPH radius = interaction cutoff | **Needs correction** | Two distinct radii |
| 5 | Variant 1 fastest, no barriers | Holds | Use for toy only |
| 5 | Variant 2 is conservative and benchmarkable | Holds | But it is an MLIP, not an automaton |
| 5 | Variant 3 is the target | Holds | Record in ADR 0003 |
| 5 | Rare events make training data unrepresentative | Holds | Promote to primary risk |
| 6 | Per-element networks break equal-and-opposite forces | **Needs correction** | Real issue is pair symmetry + data cost |
| 6 | Shared trunk + heads is the middle ground | Holds | Record in ADR 0005 |
| 6 | Orientation should come from geometry, not a per-atom parameter | Holds | Correct and important |
| 7 | Global conditioning via feature-wise modulation | Holds | Standard practice |
| 7 | Temperature belongs in the dynamics, not just as an input | Holds | Sharpen: an input-temperature model is not a PES |
| 7 | "Energy levels" is ambiguous | Holds | Define the observable first |
| 8 | Transition1x: 9.6M points, ~10k reactions, H/C/N/O | Holds | Verified; path iterates, not dynamics |
| 8 | OMol25/UMA: >100M snapshots, up to 350 atoms | Holds | Verified; add ωB97M-V ceiling |
| 8 | Training on DFT caps accuracy at DFT | Holds with nuance | Caps at a *specific functional* |
| 9 | Two evaluation tracks | Holds with nuance | Missing rate-level evaluation |
| 10 | Phase 2 toy world settles the design fork | Holds | Add kill criteria and a force-vs-endpoint arm |
| 11 | Grid points as particles for an XC functional | **Unresolved** | Plausible analogy; Skala's actual mechanism needs checking |
| 12 | Risk table | Holds with nuance | Missing six risks; see [register](../08-risk/01-risk-register.md) |
| 13 | Open questions | Holds | Add "what is the observable?" |

> **In plain words.** Most of the note is sound. Four statements would
> actively mislead a builder, and one whole category of risk is missing. Fix
> those five things and the note is a solid foundation.

## What is genuinely novel here

Stripping away the re-implementation, three things in this project are not
already done by someone else:

1. **Persistent per-atom latent state inside a conservative potential.** MLIPs
   have within-call features but no memory across steps. NCA has memory but no
   energy. The intersection is thin.
2. **A cost-targeted architecture.** The pitch is "tiny rule, many particles",
   not "big model, best accuracy". If a 10k-parameter rule can carry a real
   reaction, that is a different point on the frontier, not a worse version of
   UMA.
3. **A rigorous negative result about attractor training.** Nobody has
   published "NCA-style endpoint training suppresses barrier crossing in
   molecular dynamics". If true, it is worth writing up on its own.

Everything else — equivariance, message passing, element conditioning,
multi-fidelity learning — is well-trodden. The project should not pretend
otherwise, and should borrow aggressively.

> **In plain words.** Only three parts of this idea are actually new. Be
> ruthless about borrowing the rest, and protect those three.

## Verdict

**Proceed, with the framing changed.** The note is a strong hypothesis
document, not a plan. Its own suggested path (toy world first, then energy-based
hybrid) is correct. But it under-weights the attractor problem, mis-describes
the multi-species demo, and gives the wrong reason for rejecting per-element
networks. Fix those three, adopt the observable hierarchy, and the project has
a defensible research question.

Do not start by reproducing the NPA demo for its own sake. Start by writing the
two-species toy world and the force-vs-endpoint experiment, because that is the
cheapest test of the only assumption that could invalidate the whole idea.

## Open questions

- Does endpoint/attractor training measurably suppress barrier crossings in a
  toy potential? (Phase 2, arm C.)
- Can persistent state be trained stably when the loss includes forces, which
  penalise state-induced energy changes?
- Is the "10k parameters" claim meaningful for chemistry, or does reaction
  accuracy force a model three orders of magnitude larger?
- What is Skala's actual mechanism? The note's "points on the integration
  grid" description needs verification before the §11 extension is taken
  seriously.

## What would change this document

- A published demonstration of persistent state improving a conservative
  potential, which would raise confidence in the core claim.
- Evidence that NPA's regeneration emerges only from endpoint losses (rather
  than from the architecture), which would make the attractor objection
  weaker and the fix easier.
- A Skala methods section showing explicit grid-point message passing, which
  would make the §11 extension much more plausible.

## Sources

1. Kim, Pajouheshgar, Süsstrunk, Jakob, Park, *Neural Particle Automata:
   Learning Self-Organizing Particle Dynamics*, SIGGRAPH 2026,
   arXiv:2601.16096v3. <https://arxiv.org/abs/2601.16096> (retrieved
   2026-11-07). Sections 3.2, 4.4 and the Limitations paragraph are the
   relevant passages.
2. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry*. <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07).
3. Levine et al., *The Open Molecules 2025 (OMol25) Dataset, Evaluations, and
   Models*, arXiv:2505.08762. <https://arxiv.org/abs/2505.08762> (retrieved
   2026-11-07).
4. Luise et al., *Accurate and scalable exchange–correlation with deep
   learning* (Skala), arXiv:2506.14665. <https://arxiv.org/abs/2506.14665>
   (retrieved 2026-11-07).
5. Schreiner et al., *Transition1x — a dataset for building generalizable
   reactive machine learning potentials*, Scientific Data 9, 2022.
   <https://www.nature.com/articles/s41597-022-01870-w> (retrieved 2026-11-07).
