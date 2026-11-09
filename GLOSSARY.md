# Atomistic reaction modelling

Canonical scientific language for this project. Definitions describe domain concepts; architecture and experiment choices belong in the design documents.

## Physical description

**Configuration**: Atomic identities and positions, together with the cell and boundary conditions when relevant. A configuration alone does not specify velocities or an electronic state.
_Avoid_: Frame when no trajectory exists.

**Phase-space state**: A configuration and its nuclear momenta, with any additional physical variables needed to determine the evolution.
_Avoid_: Positions as a complete dynamical state.

**Electronic-state specification**: The electron count, spin constraints and electronic surface being modelled for a configuration. Charge and multiplicity do not always uniquely identify a surface.
_Avoid_: Energy levels as an unspecified input.

**Potential energy surface (PES)**: The electronic energy including nuclear repulsion as a function of nuclear positions for a specified electronic state.
_Avoid_: Free-energy surface as a synonym.

**Electronic activation barrier**: The energy difference between a transition state and the specified reactant reference on a PES.
_Avoid_: Rate constant, activation free energy.

**Activation free energy**: The free-energy difference between a transition-state dividing surface and a reactant ensemble under stated thermodynamic conditions.
_Avoid_: Electronic barrier when entropy and thermal effects are included.

**Reaction pathway**: A curve through configuration space connecting reactants and products. Its parameter need not represent time.
_Avoid_: Trajectory for NEB images.

**Trajectory**: An ordered evolution of a specified physical or model state with a declared time coordinate and propagation rule.
_Avoid_: Reaction pathway when only static images are available.

**Reaction event**: A transition between operationally defined reactant and product basins, with a commitment rule to reject fleeting recrossings.
_Avoid_: Bond break inferred from a single distance frame.

**Reference method**: A fully specified calculation protocol used to assign labels or assess predictions; its outputs retain numerical and physical approximation errors.
_Avoid_: Ground truth for approximate electronic-structure labels.

> **In plain words.** A photograph of atoms is different from a film of their motion. A hill on an energy map is different from the time needed to cross it. The reference calculation is a carefully chosen measuring stick, which can still be imperfect.

## Learned models

**Neural particle automaton (NPA)**: A particle system whose local learned rule updates positions and internal features through repeated applications.
_Avoid_: Reactive potential unless an energy and force contract is supplied.

**Machine-learned interatomic potential (MLIP)**: A learned model of atomistic potential energy, conventionally used with forces and a separate dynamics integrator.
_Avoid_: Exchange-correlation functional.

**Exchange-correlation functional (XC functional)**: The density-dependent component of an electronic energy functional that accounts for exchange and correlation beyond the chosen explicit terms.
_Avoid_: Interatomic potential as a synonym.

**Within-call feature**: An intermediate atomic representation computed during a single model evaluation and discarded afterwards.
_Avoid_: Memory or persistent state.

**Persistent latent state**: Learned per-particle variables retained across successive physical propagation steps; these variables need not have a unique physical interpretation.
_Avoid_: Electronic state, charge or spin unless separately justified.

**Relaxed auxiliary state**: Additional variables determined by solving a stated stationary or minimisation problem for each configuration.
_Avoid_: Persistent memory when the final answer is independent of the initial guess.

**Conservative force field**: A force field derivable from a single-valued, time-independent potential on the specified configuration domain.
_Avoid_: Energy-conserving simulation, which additionally depends on propagation and external work.

**Element conditioning**: Dependence of a shared learned interaction rule on atomic identities.
_Avoid_: Unseen-element generalisation for a newly allocated, untrained embedding.

> **In plain words.** A model can remember a calculation it is doing now, or remember what happened earlier in a film. Those are different abilities. Naming a hidden number “charge” does not make it a measured electrical charge.

## Evaluation

**Label fidelity**: The electronic-structure protocol and numerical quality of reference values.
_Avoid_: Dataset size as a proxy for accuracy.

**Deployment domain**: The chemistry, states, boundary conditions and operating conditions for which a model is intended to be used.
_Avoid_: Universal without stating coverage.

**Out-of-distribution configuration**: A configuration or state specification inadequately represented by the training distribution under a declared test criterion.
_Avoid_: Uncertain as a synonym; a model can be confidently wrong.

**Rollout stability**: Continued propagation without predefined numerical or physical failure; it does not establish accurate sampling or reaction rates.
_Avoid_: Physical accuracy as a synonym.

**Chemical accuracy**: A conventional energy-error scale, often one kilocalorie per mole; the relevant observable and tolerance must still be specified.
_Avoid_: Guaranteed correct kinetics.

> **In plain words.** A car that keeps driving has passed a reliability check, but may still be taking the wrong road. Likewise a stable simulation can give wrong science. Every claim needs to say what was tested and where it applies.
