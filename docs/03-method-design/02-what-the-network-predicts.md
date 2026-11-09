---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: []
---

# Prediction targets: updates, forces and energies

The prediction target determines which scientific questions the model can answer. A coordinate predictor, a force predictor and an energy model need different training labels, admit different failure modes and support different evaluation contracts.

**Key takeaways**

- Use a single-valued differentiable energy for the first chemistry calculator.
- Evaluate direct propagators as dynamics models with an explicit timestep.
- Do not describe arbitrary evolving-state forces as physically energy-conserving.

## Direct propagation and direct forces

A proposed direct propagator is $(R_{t+\Delta t},P_{t+\Delta t},h_{t+\Delta t})=\Phi_\theta(R_t,P_t,h_t,Z,c;\Delta t)$. Here $t$ is physical time, $\Delta t$ a declared step and $\theta$ learned parameters. A position-only input may force $h$ to infer missing velocity; apparent memory gains can then be an input-design artefact. Include a position-and-momentum baseline.

A direct force predictor $F_\theta(R)$ supports a standard integrator but need not satisfy integrability. In a simply connected smooth domain, a conservative force field requires symmetry of mixed force derivatives, $\partial F_a/\partial R_b=\partial F_b/\partial R_a$, where $a,b$ index Cartesian coordinates. Test loop work $\oint F\cdot dR$ numerically. Small test-set force MAE does not establish this property.

Without an energy head there is no directly defined electronic reaction energy or saddle barrier. One may train an additional energy estimator, but it must be checked for consistency with forces; a separately predicted number does not solve integrability. Direct models can still target structural distributions or transport, provided their equilibrium measure and physical time are validated.

> **In plain words.** A model that guesses the next film frame can look convincing without knowing the hills that caused the motion. A model that guesses pushes can also disagree with itself around a closed trip. Decide whether you need a convincing film, a consistent energy map, or both.

## Scalar energy and differentiation

For a proposed stateless model,
$$E_\theta(R,Z,c)=\sum_i\epsilon_\theta(\mathcal N_i,Z_i,c),\qquad F_i=-\nabla_{r_i}E_\theta.$$
Here $\mathcal N_i$ is a local atomic environment and $\epsilon_\theta$ an atomic energy contribution. Atomic contributions are not generally uniquely observable; the physically constrained quantity is the total energy and its derivatives. Relative-energy losses must preserve stoichiometry and reference conventions.

Energy supervision anchors offsets and reaction differences; force supervision constrains slopes. A proposed joint loss is
$$\mathcal L=w_E\langle((E-E^*)/s_E)^2\rangle+w_F\langle\| (F-F^*)/s_F\|^2\rangle.$$
Stars denote reference labels, $s_E,s_F$ declared normalisation scales and $w_E,w_F$ dimensionless weights. State whether forces are averaged per component and energies per structure or atom. Per-atom errors can conceal an unacceptable total reaction-energy error.

Automatic differentiation supplies the gradient of the implemented energy, not a guarantee that the energy is accurate. Smooth cutoffs and reliable derivatives matter. Conservativity constrains continuous dynamics, while timestep and precision govern integration error. Hamiltonian neural networks provide a useful structural precedent, not a chemistry performance guarantee [HNN].

> **In plain words.** Learning the height of the landscape lets you calculate which way a ball rolls. Height errors and slope errors both matter. Following a wrong but smooth landscape consistently still takes you to the wrong place.

## Why the evolving-state hybrid needs another contract

Suppose $E=E(R,h)$ and nuclear forces are $-\partial_R E$ while $h$ evolves by an arbitrary learned rule. For continuous dynamics with ordinary nuclear kinetic energy $K$, the chain rule gives
$$\frac{d(K+E)}{dt}=\frac{\partial E}{\partial h}\cdot\dot h.$$
The position terms cancel; the latent-state term generally does not. This is a project derivation, not an empirical result. Even if forces are conservative at each fixed $h$, they need not arise from one time-independent PES along the actual trajectory.

Three defensible alternatives are: solve $h^*(R)$ to stationarity at each geometry; give auxiliary variables a justified extended Hamiltonian and report the corresponding conserved quantity; or describe the model explicitly as dissipative/stochastic and validate its target distribution and work/heat accounting. For the stationary case, $E_\mathrm{eff}(R)=E(R,h^*(R))$ requires a unique or carefully specified branch. At exact stationarity the auxiliary chain-rule term vanishes; at finite residual it may not. Implicit differentiation or unrolling a fixed solver must match the actual energy contract. Warm starts should not change the converged answer.

**Recommendation (inference):** V2 is the reference architecture. Test V3a only after energy and force consistency is demonstrated. Reject “hybrid is conservative by construction” without qualifying which variables are fixed and which energy is conserved.

> **In plain words.** Imagine a ball rolling while someone secretly raises the floor beneath it. The slope can be perfectly calculated at every instant, yet the ball gains energy from the moving floor. A hidden state that changes the energy map can do the same thing.

## Promotion criteria

Promote a direct update only if it preserves the declared target statistics, stable physical time and useful cost. Promote an energy model only after force finite differences, symmetry, smoothness, size consistency and rollout checks. Promote state only if it adds value against both a stateless model and the same recurrent computation reset at every call. See [latent-state tests](05-latent-state-and-time-mapping.md).

> **In plain words.** Each model gets an exam suited to its promise. A film generator and a surveying instrument do different jobs. Passing one exam does not grant the other qualification.

## Open questions

- Is inference state reset, converged, or physically propagated?
- Which energy derivative is implemented when auxiliary states depend on geometry?

> **In plain words.** These are choices that the current evidence does not settle. Write down the answer before spending money on an experiment that depends on it. An empty result is better than an invented answer.

## What would change this document

- A demonstrated need for dissipative or electronically excited dynamics.
- A validated extended-system derivation.

> **In plain words.** Treat this document like a map made before the expedition. New measurements can reveal a better route. Record what changed and why when that happens.

## Sources

- [Greydanus et al., Hamiltonian Neural Networks](https://arxiv.org/abs/1906.01563) (retrieved 2026-11-07).
- [Ko et al., fourth-generation neural potentials, full paper](https://arxiv.org/html/2009.06484) (retrieved 2026-11-07).
- [ASE molecular dynamics documentation](https://docs.ase-lib.org/ase/md.html) (retrieved 2026-11-07).
