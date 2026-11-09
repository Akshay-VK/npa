---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: []
---

# Symmetry, equivariance and conservation

Physical symmetries constrain both predictions and tests. This document separates energy invariance, force equivariance, continuous conservation laws and the numerical behaviour of a simulated trajectory.

**Key takeaways**

- Enforce geometric symmetry structurally where practical.
- Differentiate one invariant total energy to obtain forces.
- Treat momentum, angular momentum and energy as distinct checks.

## Transformation contract

For an isolated field-free system with transformation $r_i\mapsto Qr_{\pi(i)}+a$, $Q$ is an orthogonal rotation or reflection, $a$ a translation and $\pi$ a permutation that carries atom identity with coordinates. Require energy invariance and forces to rotate and permute correspondingly. In a periodic system transform the cell too; in an applied field transform the field if testing coordinate covariance. Rotating positions alone while keeping a physical field fixed changes the problem.

Scalars, vectors and higher-order tensors transform differently. Cartesian gradient components fed into an unrestricted MLP do not automatically respect rotations. The NPA paper explicitly says it does not enforce rotational equivariance [NPA, §3.2.2]. It also pursues spatial-scale and sampling-density generalisation. These are not atomistic physical symmetries: changing bond lengths or atom counts generally changes the system.

Distance-only invariant descriptors are rotationally safe but must retain enough angular and many-body information for chemistry. Equivariant hidden features are one way to obtain expressive geometry handling [NEQ]. They are not the only possible invariant-energy construction.

> **In plain words.** Turning a molecule in an empty room should turn its forces without changing its energy. Stretching the molecule is a different experiment and should change the answer. A picture model that resizes shapes successfully has not learned this chemical distinction.

## Which symmetry gives which conserved quantity

For a differentiable scalar energy with no external positional dependence, uniform translation leaves $E$ unchanged. Differentiating that identity yields $\sum_iF_i=0$. Rotation invariance similarly gives zero net internal torque, $\sum_i r_i\times F_i=0$. These are structural project derivations under the stated assumptions.

Do not require every many-body contribution to have a unique pair-force decomposition. Equal-and-opposite central pair forces are sufficient for certain pair models, not a necessary representation of all valid molecular forces. One jointly differentiated many-body energy is the more general contract.

A time-independent energy plus exact Hamiltonian evolution conserves total energy. A finite-step integrator approximates that evolution; stochastic thermostats and barostats exchange energy with a reservoir. Energy conservation should therefore be assessed in a suitable NVE test, separately from NVT distribution checks. Frozen atoms, walls and external fields change which momentum balances are expected.

> **In plain words.** A group of people pushing only each other cannot move its centre by internal pushing. But a wall can push the group from outside. Before accusing a simulation of breaking a rule, check whether its surroundings supply a push or energy.

## Smoothness, locality and expressivity

A neighbour graph changes as atoms cross the cutoff. Choose radial envelopes with sufficient vanishing derivatives at that boundary for forces and any higher derivatives needed. Hard nearest-neighbour selection can introduce discontinuities even when the neural layers themselves are smooth. Cap neighbour counts only with an explicit overflow strategy; silently dropping close neighbours changes the model.

An SPH density is a modelling descriptor, not an electronic density. Kernel normalisation that improves robustness to particle resampling can erase physically meaningful atomic coordination. Compare sum and normalised aggregation on environments with different neighbour counts. Design collision and isolated-atom tests, not just equilibrium geometries. Higher body-order representations are established alternatives; model depth alone does not describe expressivity [MACE].

> **In plain words.** A road should not suddenly jump in height at an invisible border. A force model needs smooth borders too. Also, averaging a crowd can hide whether two people or twenty people are present, even though chemistry cares about the count.

## Acceptance test procedure

For held-out geometries, generate translations, rotations, reflections and allowed atom permutations. Evaluate transformed energy and inverse-transformed forces, comparing discrepancies with floating-point and finite-difference noise. Test cell transformations separately. Measure total force and torque in an isolated unconstrained system, then integrate with successively smaller timesteps. Select tolerances from an analytic reference run and the target observable rather than declaring a universal magic tolerance. Record the precision and kernel implementation.

> **In plain words.** Make several equivalent copies of the same problem and compare answers. Differences should come only from normal calculation noise. Then make the simulation steps smaller to see whether remaining errors are caused by the stepping procedure.

## Open questions

- Which equivariant tensor types and boundary conditions are supported?
- Are Hessians needed, or only first derivatives?

> **In plain words.** These are choices that the current evidence does not settle. Write down the answer before spending money on an experiment that depends on it. An empty result is better than an invented answer.

## What would change this document

- A deployment setting with magnetic fields, constrained surfaces or explicit symmetry breaking.
- Measured smoothness or kernel precision failures.

> **In plain words.** Treat this document like a map made before the expedition. New measurements can reveal a better route. Record what changed and why when that happens.

## Sources

- [Kim et al., Neural Particle Automata, full paper v3](https://arxiv.org/html/2601.16096v3) (retrieved 2026-11-07).
- [Batzner et al., NequIP](https://arxiv.org/abs/2101.03164) (retrieved 2026-11-07).
- [Batatia et al., MACE](https://arxiv.org/abs/2206.07697) (retrieved 2026-11-07).
- [ASE molecular dynamics documentation](https://docs.ase-lib.org/ase/md.html) (retrieved 2026-11-07).
