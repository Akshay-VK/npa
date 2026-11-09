---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: [01-project-charter.md]
---

# What you need to know personally

This is the honest gap analysis. Not the reading list — the *internal model*
you need before you can tell a good result from a plausible-looking bad one.
It is written on the assumption that you are technically strong, comfortable
with machine learning, and not a trained quantum chemist. That combination is
workable, but only if you know exactly which intuitions you are missing.

**Bottom line**

- You need four mental models: energy landscapes, ensembles, error cancellation,
  and the difference between interpolation and extrapolation. Everything else
  is lookup.
- You do **not** need to derive coupled cluster. You do need to know when a
  number labelled "CCSD(T)" is not trustworthy.
- The skill that will save you most time is *unit and magnitude sanity
  checking*. Most bad results are physically absurd before they are
  statistically wrong.
- The skill that will cost you most time if missing is *experimental design*:
  knowing what a result would falsify before you run it.
- Budget real time for one thing that feels unproductive: reading the primary
  papers, not the blog posts about them.

## The four mental models

### 1. The energy landscape is the object

A molecule is not a set of balls on springs. It is a point moving on a
high-dimensional surface whose height is the electronic energy. Bonds are
valleys. Reactions are mountain passes. Temperature is the jitter that
occasionally gets you over a pass.

Almost every confusion in this field dissolves once you hold this picture:
"why is the barrier important?" (it sets the rate), "why is a stable molecule
stable?" (it sits in a local minimum), "why does the model need forces?"
(forces are the slope of the surface), "why can't we just predict the product?"
(because the product is wherever the trajectory falls, not a label).

What you must be able to do: sketch a one-dimensional slice through a reaction
and label reactant, transition state, product, barrier height, reaction energy.
If you cannot, read
[electronic structure primer](../01-science/01-electronic-structure-primer.md)
before anything else.

> **In plain words.** Imagine a landscape with valleys and mountain passes.
> Molecules sit in valleys. Reactions happen when they get enough of a shove to
> cross a pass. The height of the pass controls how often that happens. Almost
> everything else is detail about the shape of the landscape.

### 2. Ensembles, not single molecules

A single trajectory is not a prediction. Chemistry happens to *populations*.
Temperature is a property of the ensemble. A rate constant is an average over
many trajectories. A free energy is a property of a distribution, not of a
configuration.

This matters because a model evaluated on one geometry is not thereby
evaluated on chemistry. It also matters because thermostats, which look like
numerical conveniences, actually change the dynamics and can change the answer.

What you must be able to do: explain why a 300 K simulation and a 300 K
calculation of the same barrier can give different rates, and what a thermostat
does to the trajectory that the potential does not.

> **In plain words.** One molecule doing one thing tells you very little.
> Chemistry is about what millions of molecules do on average. That is why
> "temperature" is not just a number you type in; it describes the whole crowd.

### 3. Error cancellation is the hidden variable

Quantum chemistry gets accurate numbers by cancelling large errors, not by
computing small ones. A total energy might be wrong by hundreds of kcal/mol
while a reaction energy from the same calculation is right to one. This is why
absolute energies are almost never the metric, and why "chemical accuracy"
means 1 kcal/mol on a *difference*.

The practical consequence: a model can look excellent on total energies and
fail on differences, or vice versa. Always ask *what difference* the number
is a difference of.

What you must be able to do: given a table of method errors, say whether the
errors will cancel in the observable you care about.

> **In plain words.** Two wrong numbers can subtract to give a right one. That
> is not a trick; it is how most of computational chemistry works. So "the
> total energy is wrong by 300" and "the reaction energy is right to 1" are not
> contradictory, and you must always ask which one is being reported.

### 4. Interpolation is not extrapolation

A neural network trained on configurations near equilibrium has seen nothing
like a bond at 3 Å. It will still produce a number there, confidently. The
number will be meaningless. This is the defining failure mode of the entire
field, and it is invisible in a random train/test split.

What you must be able to do: design a split that tests extrapolation (unseen
reaction, unseen element pair, unseen temperature) rather than interpolation,
and recognise when someone has not.

> **In plain words.** A model that has only seen cats and dogs will still
> confidently call a horse a dog. It does not know it is out of its depth.
> The only defence is to test it on things it has never seen, on purpose.

## The five things that will actually bite you

Ordered by expected time lost, not by intellectual importance.

**1. Units.** Hartree versus eV versus kcal/mol versus kJ/mol; ångström versus
bohr; force in eV/Å versus hartree/bohr. A factor of 27.2 hides in every
conversion. Keep [the units card](../01-science/07-units-scales-and-orders-of-magnitude.md)
open. Most "the model is broken" incidents are unit errors.

**2. Reference levels.** "DFT" is not one method. "CCSD(T)" is not one number.
A dataset labelled "ωB97M-V/def2-TZVPD" cannot support a claim of beating
ωB97M-V. Before using any dataset, write down its level of theory and decide
what claims that level can support.

**3. Data leakage.** Datasets overlap. GMTKN55 subsets appear in training sets.
Transition1x reaction families appear in pretraining corpora. A suspiciously
good result on a public benchmark is guilty until proven innocent.

**4. Statistical power.** Three seeds and a mean are not evidence. A 0.2 kcal/mol
improvement with a 0.4 kcal/mol standard deviation across seeds is noise. Decide
the effect size you care about, compute the number of seeds needed, and run that
many.

**5. The attractor trap.** Described in
[the critical assessment](03-critical-assessment-of-the-idea-note.md). A model
trained to reach a target will resist leaving it. This is invisible in
single-point metrics and fatal in dynamics.

> **In plain words.** Units, data provenance, leakage, and sample size account
> for most wasted weeks. None of them are intellectually hard. All of them are
> easy to skip when you are excited about a result.

## What you can safely not learn

- The derivation of the coupled-cluster equations. Know what they cost and
  what they miss; that is enough.
- Density functional theory's mathematical foundations. Know that the functional
  is unknown, that it is fitted, and that its errors are systematic, not random.
- Group theory and irreducible representations. Useful for equivariant
  architectures, but you can use a library that handles it.
- Fortran, MPI, and the internals of VASP. You will call these, not modify them.

> **In plain words.** You do not need to be able to build a car to drive one.
> Learn what the pedals do, where the fuel goes, and which warning lights mean
> stop.

## What you must learn that is not obvious

- **How to read a computational chemistry paper's methods section.** The
  abstract gives the result; the methods section gives the protocol; the
  supporting information gives the caveats. Read them in reverse order.
- **How a benchmark can be gamed without cheating.** Fitting to a benchmark,
  selecting the best of many functionals, and evaluating on the training
  distribution are all legitimate practices that produce illegitimate
  confidence.
- **How to run a negative control.** A null model — a constant predictor, a
  linear model, a shuffled-label model — tells you whether your result is
  better than nothing. Most ML papers in this space would benefit from one.
- **How to estimate compute before running.** One DFT single point is seconds;
  one NEB path is hours; one AIMD trajectory is days. Knowing this stops you
  designing experiments you cannot afford.

> **In plain words.** The four skills that separate a good computational
> scientist from a good machine-learning engineer are: reading methods
> sections, spotting benchmark tricks, running controls, and costing a job
> before starting it.

## A 30-day curriculum

Not a reading list — a sequence of things to *do*, because these intuitions do
not transfer by reading.

| Days | Do this | You will learn |
|---|---|---|
| 1–3 | Install PySCF, compute the energy of H₂ at ten bond lengths, plot the curve | What a PES is, what a basis set does, what "the minimum" means |
| 4–6 | Compute the barrier of H + H₂ with a cheap method and an expensive one | Error cancellation, method sensitivity |
| 7–9 | Run a 1 ps Langevin MD trajectory of a small molecule in ASE | Timesteps, thermostats, what a trajectory file contains |
| 10–12 | Train a tiny neural network to fit forces from that trajectory | Interpolation, overfitting, the difference between energy and force loss |
| 13–16 | Reproduce the NPA 2D morphogenesis demo | SPH perception, the update rule, what the paper's code actually does |
| 17–20 | Build the two-species toy world from [experiment protocols](../07-delivery/02-experiment-protocols.md) | The real engineering: neighbour lists, rollouts, stability |
| 21–24 | Run the force-loss versus endpoint-loss comparison | The attractor trap, empirically |
| 25–30 | Write it up as if for a sceptical reviewer | What you actually understood |

> **In plain words.** Thirty days of doing, in this order, will teach you more
> than three months of reading. The point is to feel the failure modes in your
> hands, not to memorise them.

## How to tell whether you understand something

A simple test, applied to any claim in these documents: can you explain it to
a smart person outside the field, without using a word you cannot define, and
without the explanation collapsing into "because the maths says so"? The
plain-words blocks are the authors' attempt. If you cannot do it yourself for
the thing you are about to build, you are not ready to build it.

Second test: can you state what observation would prove you wrong? If not, you
have a belief, not a hypothesis.

> **In plain words.** If you cannot explain it simply, and cannot say what
> would prove you wrong, you do not understand it yet — you have just got used
> to it.

## Open questions

- What is the reader's actual background? This document assumes ML fluency and
  chemistry unfamiliarity; if that is backwards, the curriculum should be
  reordered.
- Is there a collaborator who can supply the domain judgement, which would
  change "what you must learn" into "what you must ask"?

## What would change this document

- If the project hires or collaborates with a computational chemist, the
  curriculum shrinks to the ML half and the four mental models.
- If phase 2 shows the architecture is unworkable, the curriculum's second half
  becomes a study of why, which is still worth doing.

## Sources

This document is pedagogical synthesis rather than factual claim. The physical
statements it relies on are sourced in
[the science cluster](../01-science/01-electronic-structure-primer.md) and
[the units card](../01-science/07-units-scales-and-orders-of-magnitude.md).
