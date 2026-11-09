---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: []
---

# Latent state, identifiability and physical time

Persistent state is the proposed distinctive ingredient, so it needs the strongest experimental scrutiny. This document defines what state means, how it is initialised, and which experiments distinguish useful memory from missing inputs or numerical hysteresis.

**Key takeaways**

- Separate message-passing iterations from physical time steps.
- Test resets and alternate histories at fixed geometry.
- Do not infer time from a path-image index.

## State categories and their meanings

Within-call features are recomputed for each energy evaluation. A relaxed auxiliary state solves a geometry-dependent electronic or surrogate problem; it may use a warm start but should converge to the declared branch. A persistent dynamical state carries information from earlier physical steps. A true electronic population or spin degree of freedom has its own physical interpretation and evolution equation. Calling all of these “hidden state” conceals a substantive modelling decision.

State dimensions generally have no unique interpretation: a learned change of basis can preserve predictions. Charge or spin auxiliary losses can anchor some outputs but depend on reference conventions. A charge partition is not uniquely determined by energy and forces. Keep unconstrained feature channels unnamed; assess whether auxiliary supervision improves the main observable rather than merely making channels look interpretable.

> **In plain words.** Working notes used during a calculation are different from a diary of earlier events. A diary entry is also different from a measured physical property. Name the kind of memory before claiming what it represents.

## Initialisation, restart and permutation

Specify an initializer $h_0=g_	heta(R_0,Z,c)$ or a fixed declared state, a burn-in procedure if any, and exactly which variables a restart checkpoint contains. A persistent state must follow atom identities through permutation and neighbour-list rebuilding. Padding and batching must not let one molecule inherit another molecule’s history. Fragment separation must not leave a hidden communication channel through pooled global state unless the intended physical model calls for it.

Evaluate cold starts, warm starts and independent restart continuation. For a PES model, run the same geometry from different initial states to the stated convergence tolerance; compare energies, forces, residuals and iteration counts. If multiple branches survive, define their physical meaning or fail the calculator contract. These tests are proposed here and have not been run.

> **In plain words.** A paused film should resume from the saved scene without characters swapping memories. A fresh unrelated film should not inherit those memories. If the same still photograph gets different energy answers depending on the previous film, investigate before trusting it.

## Time is a calibrated quantity

A learned step has no intrinsic femtosecond value. For a direct propagator define $\Delta t$ in the training target and record saved-frame spacing, which may differ from the integration timestep. Test the composition relation $\Phi_{2\Delta t}(x)\approx\Phi_{\Delta t}(\Phi_{\Delta t}(x))$ only for deterministic dynamics with matching state and protocol. Here $x$ is the complete model state and $\Phi$ its learned propagator. For stochastic dynamics compare distributions; identical random numbers are not automatically the correct noise coupling across step sizes.

For energy-based models a standard integrator defines time [ASE]. Latent relaxation iterations are solver work, not elapsed nuclear time. NEB images are path optimisation outputs [NEB], so their index cannot supply velocities, rates or physical timestep labels. Do not train a physical recurrent update across these images as though they were a trajectory.

Adaptive stepping requires an error estimator and a method consistent with the intended dynamics and sampling. “Take bigger jumps when little happens” does not solve the rare-event rate problem. Large steps can miss fast vibrations or distort barrier crossings.

> **In plain words.** One page turn in a picture book does not mean one second has passed. Some pages show consecutive moments; others show a planned route. A simulation needs a clock tied to its equations or its training data.

## Decisive experiments for memory

Run a stateless energy model, a within-call iterative model, a warm-started converged model and a persistent-state model at matched measured inference cost. Add a reset-at-every-physical-step version of the persistent model. Give all dynamics models explicit velocity or momentum inputs if their target requires them. Randomly shuffle trajectory ordering only for models claiming not to require history.

Construct converging histories that end at the same geometry and physical state. For ground-state energy prediction require agreement; for a reduced process test whether history improves future distributions rather than arbitrary coordinate matching. Memory in projected dynamics has a rigorous theoretical motivation [MEM], but transferring that motivation to fully resolved ground-state atoms is an inference. Stop if gains disappear after supplying missing momenta or matching computation.

> **In plain words.** Ask whether the diary helps after the student already has all the information needed today. Compare it with simply allowing more thinking time. If the advantage vanishes, the experiment has identified the real source of improvement.

## Open questions

- Is the intended target ground-state dynamics, coarse-grained dynamics, or excited-state dynamics?
- What complete checkpoint is needed for restart?

> **In plain words.** These are choices that the current evidence does not settle. Write down the answer before spending money on an experiment that depends on it. An empty result is better than an invented answer.

## What would change this document

- A controlled history-dependent task with observed state variables.
- Evidence that warm starts reduce cost without introducing hysteresis.

> **In plain words.** Treat this document like a map made before the expedition. New measurements can reveal a better route. Record what changed and why when that happens.

## Sources

- [Izvekov, Mori–Zwanzig coarse-grained dynamics](https://doi.org/10.1103/PhysRevE.104.024121) (retrieved 2026-11-07).
- [ASE molecular dynamics documentation](https://docs.ase-lib.org/ase/md.html) (retrieved 2026-11-07).
- [ASE nudged elastic band documentation](https://docs.ase-lib.org/ase/neb.html) (retrieved 2026-11-07).
