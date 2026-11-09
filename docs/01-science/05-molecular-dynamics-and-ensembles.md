---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-electronic-structure-primer.md, 04-reaction-kinetics-and-rare-events.md]
---

# Molecular dynamics and ensembles

A potential energy surface is a static object. Dynamics is what happens when
you put atoms on it with momentum and let them move. Most ML-for-chemistry
papers quietly elide this step, which is why claims about "simulating
reactions" often turn out to mean "computing energies at geometries someone
else generated". This document covers the actual machinery: integrators,
timesteps, thermostats, ensembles, and the operational meaning of "trajectory".

**Bottom line**

- Newton's equations, integrated with velocity Verlet, are the default. The
  timestep is set by the fastest vibration: ~1 fs for bonds involving hydrogen,
  2 fs with constraints.
- A thermostat is not a cosmetic choice. It changes the dynamics, and different
  thermostats give different transport properties and different rates.
- NVE, NVT, and NPT are different physical situations, not different settings.
  Report which one you used.
- Energy conservation in NVE is the sharpest test of an energy-based model, and
  it is trivially checkable.
- A trajectory file is positions (and usually velocities) at a sequence of
  times. If a paper does not say how it was generated, the trajectory is not
  evidence.

## The equations being integrated

For $N$ atoms with masses $m_i$,

$$
m_i \ddot{\mathbf{x}}_i = \mathbf{F}_i = -\frac{\partial E}{\partial \mathbf{x}_i}.
$$

Velocity Verlet, one step of length $\Delta t$:

1. $\mathbf{v}(t + \tfrac12 \Delta t) = \mathbf{v}(t) + \tfrac12 \Delta t\, \mathbf{F}(t)/m$
2. $\mathbf{x}(t + \Delta t) = \mathbf{x}(t) + \Delta t\, \mathbf{v}(t + \tfrac12 \Delta t)$
3. recompute $\mathbf{F}(t + \Delta t)$
4. $\mathbf{v}(t + \Delta t) = \mathbf{v}(t + \tfrac12 \Delta t) + \tfrac12 \Delta t\, \mathbf{F}(t+\Delta t)/m$

Properties that matter:

- **Time-reversible** and **symplectic**. It conserves a shadow Hamiltonian
  exactly, which is why energy drift is bounded rather than secular.
- **Two force evaluations per step.** The dominant cost.
- **Requires a smooth force field.** A discontinuity in $\mathbf{F}$ produces a
  discontinuity in energy that the integrator cannot absorb.

Alternatives: leapfrog (equivalent to Verlet, different bookkeeping), and
higher-order symplectic integrators (better energy conservation at large
timesteps, more force evaluations). For this project, velocity Verlet is the
right default and there is no reason to be clever.

> **In plain words.** Push every atom a tiny bit in the direction its force
> points, then recompute the forces, then push again. The magic is that this
> simple loop conserves energy to high accuracy as long as the steps are small
> enough.

## Choosing a timestep

The timestep must resolve the fastest motion in the system. The fastest motion
is almost always a bond stretching vibration involving hydrogen.

| Bond | Approximate frequency | Period | Safe timestep |
|---|---|---|---|
| O–H stretch | ~3600 cm⁻¹ | ~9 fs | 0.5 fs |
| C–H stretch | ~3000 cm⁻¹ | ~11 fs | 1 fs |
| C–C stretch | ~1000 cm⁻¹ | ~33 fs | 2 fs |
| Heavy-atom torsion | ~100 cm⁻¹ | ~330 fs | 5 fs |

Rules of thumb:

- **1 fs** for all-atom systems with hydrogen, unconstrained.
- **2 fs** with SHAKE/LINCS constraints on bonds involving hydrogen.
- **0.5 fs** during reactive events, where bond order changes rapidly.
- **Never** choose a timestep because it makes the simulation finish faster.

*(inference)* For a learned potential, the timestep also has to resolve the
*model's* fastest feature, not just the physical one. A network with sharp
non-linearities can have effective frequencies higher than any real bond. Start
conservative (0.5 fs) and increase only after checking energy conservation.

> **In plain words.** If you take steps that are too big, you step over the
> wiggles and the simulation explodes. Hydrogen wiggles fastest, so it sets the
> speed limit.

## Ensembles

| Ensemble | What is held fixed | What it models | Common integrator |
|---|---|---|---|
| **NVE** | $N$, $V$, $E$ | Isolated system | Velocity Verlet |
| **NVT** | $N$, $V$, $T$ | System in a heat bath | Langevin, Nosé–Hoover |
| **NPT** | $N$, $P$, $T$ | System at constant pressure | Parrinello–Rahman, MTK |
| **NPH** | $N$, $P$, $H$ | Adiabatic pressure coupling | Rarely used |

These are not interchangeable. A reaction rate computed in NVT with a strong
thermostat can differ from the NVE rate, because the thermostat removes the
energy released by the reaction. For a barrier height, the ensemble matters
less; for a rate or a mechanism, it can matter a lot.

**Thermostats, in order of intrusiveness:**

- **Langevin** — adds friction and random noise. Correct canonical sampling,
  destroys the deterministic trajectory. Good for equilibration and for
  sampling; bad for mechanism studies unless the friction is small.
- **Nosé–Hoover** — deterministic, extended variable, has a conserved quantity.
  Good for equilibrium properties. Can fail to be ergodic for stiff systems.
- **Andersen** — stochastic collisions. Correct canonical sampling, unphysical
  dynamics.
- **Berendsen** — weak coupling, fast equilibration, **wrong** fluctuations.
  Widely used, widely abused. Do not use it for production statistics.
- **Bussi–Donadio–Parrinello** — stochastic velocity rescaling, correct
  canonical distribution. A good default.

> **In plain words.** A thermostat is a fake heat bath. It keeps the
> temperature where you asked, but it also meddles with the motion. Some
> thermostats meddle gently, some roughly, and one of the popular ones gets the
> fluctuations wrong.

## What "trajectory" means operationally

A trajectory is:

1. **A state**: positions, and usually velocities, for every atom.
2. **A propagation rule**: the integrator and its timestep.
3. **A boundary condition**: vacuum, periodic, or a wall.
4. **An ensemble**: what is being held fixed.
5. **A time coordinate**: the physical time each frame corresponds to.

If any of the five is missing, the file is a sequence of geometries, not a
trajectory. This distinction matters because Transition1x contains geometries
without velocities or time: it is a set of path points, not a trajectory (see
[reactive potentials](../02-prior-art/07-reactive-potentials-and-enhanced-sampling-models.md)).

**File formats.** XYZ holds positions only. Extended XYZ can hold forces and
energies. ASE trajectories (`.traj`) hold positions, velocities, and metadata.
LAMMPS dump files hold everything but in a custom format. For this project, ASE
`Extxyz` is the right default: readable, self-describing, and widely supported.

> **In plain words.** A pile of snapshots is not a movie. A movie needs a
> camera speed and a rule for what happens between frames.

## Periodic boundaries and cutoffs

In a periodic simulation, an atom leaving one side re-enters the other. The
practical consequences:

- **Minimum image convention**: each pair interacts through the nearest image.
  Only valid when the cutoff is less than half the box length.
- **Cutoff + switching function**: the potential is smoothly taken to zero at
  $r_c$, so forces are continuous. A hard truncation injects energy.
- **Long-range electrostatics** require Ewald summation or a fast multipole
  method; a plain cutoff is qualitatively wrong for ionic systems.
- **Finite-size effects**: a small box constrains fluctuations and can suppress
  or enhance a reaction. Test box-size dependence.

*(inference)* For a gas-phase reaction project, most of this is avoidable: run
in vacuum with a large box and no periodicity. Do that until there is a reason
not to. Periodic boundaries bring a large amount of subtlety for no benefit if
the target is an isolated molecule.

> **In plain words.** If you simulate a box that repeats forever, you have to be
> careful at the edges, and you have to be careful that the box is big enough
> not to interfere with itself. For single molecules in gas phase, skip the box.

## The tests every energy-based model must pass

These are cheap and they catch most integration bugs.

| Test | Procedure | Pass |
|---|---|---|
| **NVE energy conservation** | Run 10⁴ steps, no thermostat | Drift < 0.1% of mean kinetic energy |
| **Momentum conservation** | Same run, isolated | Total momentum constant to machine precision |
| **Time reversibility** | Run forward $n$ steps, negate velocities, run back | Return to start within tolerance |
| **Rotational invariance** | Rotate the whole system, compare $E$ | Difference < 1e-4 eV |
| **Translational invariance** | Shift the whole system | Difference < 1e-6 eV |
| **Force–energy consistency** | Finite-difference the energy, compare to forces | Relative error < 1e-3 |
| **Dissociation limit** | Separate fragments to 20 Å | $E \to \sum E_{\text{fragments}}$ |

These are implemented as an automated battery in
[rollout stability and physics tests](../05-evaluation/03-rollout-stability-and-physics-tests.md).
A model that fails any of them should not be used for dynamics, regardless of
its validation loss.

> **In plain words.** Seven checks, each a few minutes of compute. They catch
> almost every "the model is broken" bug before it becomes a wrong scientific
> claim.

## What changes when the potential is learned

Four differences from a classical force field:

1. **Cost is not uniform.** A neural potential's cost depends on neighbour
   count and system size in a way a Lennard-Jones potential does not. Timestep
   selection must account for per-step latency, not just physics.
2. **Smoothness is not guaranteed.** ReLU networks are piecewise linear; their
   second derivative is a sum of delta functions. This can matter for
   thermostats and for any method that uses the Hessian.
3. **Errors are correlated in time.** A learned potential's error at step $t$
   is not independent of its error at step $t-1$, because the configuration is
   similar. This makes naive error propagation estimates overconfident.
4. **Out-of-distribution states are reachable.** A trajectory can wander into a
   region the model has never seen, and the model will produce a smooth,
   confident, wrong force that pushes it further out. Classical force fields
   diverge instead, which is safer.

Point 4 is the reason for uncertainty quantification and for the stability
envelope concept: define the temperature and timestep range in which the model
has been validated, and refuse to run outside it.

> **In plain words.** A classical force field blows up loudly when you leave
> its comfort zone. A neural one leaves quietly and takes you somewhere wrong.
> That is worse.

## Open questions

- Should the project use a Langevin thermostat throughout, for simplicity and
  correct sampling, accepting that it changes the dynamics?
- How much does the choice of integrator matter for a model whose forces are
  only approximately conservative?
- Is a 1 fs timestep defensible for a reactive model where bond order changes
  within a few steps?

## What would change this document

- Evidence that the target reactions are fast enough to be observed in
  unenhanced MD at accessible temperatures, which would remove the need for the
  enhanced-sampling layer.
- A published demonstration that learned potentials require substantially
  smaller timesteps than classical ones, which would change the cost model.

## Sources

1. Verlet, *Computer "experiments" on classical fluids*, Phys. Rev. 159, 98
   (1967). <https://doi.org/10.1103/PhysRev.159.98> (retrieved 2026-11-07).
2. Frenkel and Smit, *Understanding Molecular Simulation*, 2nd ed., Academic
   Press (2002). Chapters 4–6 and 15.
3. Nosé, *A molecular dynamics method for simulations in the canonical
   ensemble*, Mol. Phys. 52, 255 (1984).
   <https://doi.org/10.1080/00268978400101201> (retrieved 2026-11-07).
4. Bussi, Donadio and Parrinello, *Canonical sampling through velocity
   rescaling*, J. Chem. Phys. 126, 014101 (2007).
   <https://doi.org/10.1063/1.2408420> (retrieved 2026-11-07).
5. Ryckaert, Ciccotti and Berendsen, *Numerical integration of the Cartesian
   equations of motion of a system with constraints* (SHAKE), J. Comput. Phys.
   23, 327 (1977). <https://doi.org/10.1016/0021-9991(77)90098-5> (retrieved
   2026-11-07).
6. Larsen et al., *The Atomic Simulation Environment*, J. Phys. Condens. Matter
   29, 273002 (2017). <https://doi.org/10.1088/1361-648X/aa680e> (retrieved
   2026-11-07).
