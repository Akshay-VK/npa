---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: []
---

# Electronic structure: what an atomistic model replaces

The central question is what physical object an atomistic NPA would approximate. Electronic structure supplies the energy landscape and its derivatives; nuclear dynamics supplies motion on that landscape. Confusing these objects makes a plausible animation look like a chemical prediction. This tutorial establishes the simplest defensible target and the circumstances where that target is insufficient.

**Actionable takeaways**

- Start by declaring composition, total charge, electronic state and the treatment of nuclei; coordinates alone do not identify every molecular energy.
- Treat a ground-state energy model as an approximation to a potential energy surface, not as an explicit simulation of electrons.
- Use H + H₂ as an open-shell doublet example. A neutral-singlet-only pipeline cannot represent its entrance channel correctly.
- Keep electronic barriers, zero-point-corrected barriers and free-energy barriers in separate fields.
- Treat persistent hidden state as a proposed modelling mechanism whose physical interpretation must be demonstrated.

## The molecular Hamiltonian, term by term

A wavefunction is an amplitude over particle positions and spins, rather than a cloud of small classical electron trajectories. For stationary states, the Schrödinger equation is $\hat H\Psi=\mathcal E\Psi$: $\hat H$ is the energy operator, $\Psi$ the molecular wavefunction and $\mathcal E$ its eigenvalue. In nonrelativistic atomic units, with no external field,

$$
\hat H=-\sum_A\frac{1}{2M_A}\nabla_A^2
-\frac12\sum_i\nabla_i^2
-\sum_{iA}\frac{Z_A}{|\mathbf r_i-\mathbf R_A|}
+\sum_{i<j}\frac{1}{|\mathbf r_i-\mathbf r_j|}
+\sum_{A<B}\frac{Z_AZ_B}{|\mathbf R_A-\mathbf R_B|}.
$$

Indices $A,B$ label nuclei and $i,j$ electrons; $\mathbf R_A,\mathbf r_i$ are their positions; $M_A$ is nuclear mass in electron-mass units; $Z_A$ is nuclear charge; and $\nabla^2$ is the Laplacian over the indicated position. The terms are nuclear kinetic energy, electron kinetic energy, electron–nucleus attraction, electron repulsion and nuclear repulsion. Atomic units absorb the electron mass, elementary charge, reduced Planck constant and Coulomb prefactor. See [Psi4's explicit electronic Hamiltonian](https://psicode.org/psi4manual/master/scf.html) and [the units card](07-units-scales-and-orders-of-magnitude.md) for conventions.

The electronic wavefunction must change sign when identical electrons are exchanged. Electron spin is part of its arguments even though it is suppressed in the equation. The displayed Hamiltonian omits spin–orbit coupling and other relativistic contributions. Those omissions are assumptions to reconsider for heavier precursor elements, not errors that a larger network automatically repairs.

For neutral matter, the electron count is the sum of nuclear charges. More generally, $N_e=\sum_A Z_A-Q$, where $N_e$ is electron count and $Q$ is signed molecular charge in elementary-charge units. Removing an electron increases $Q$. A dataset must preserve that convention.

> **In plain words.** The molecular Hamiltonian is the rulebook for a collection of nuclei and electrons. It counts motion, attractions and repulsions. Changing the number of electrons changes the game even when every nucleus stays in the same place. A model must know which game its training examples describe.

## Born–Oppenheimer separation and the energy landscape

Freeze the nuclear positions $\mathbf R=(\mathbf R_A)_A$ and solve

$$
\hat H_e(\mathbf R)\psi_n(\mathbf r;\mathbf R)
=\epsilon_n(\mathbf R)\psi_n(\mathbf r;\mathbf R),\qquad
E_n(\mathbf R)=\epsilon_n(\mathbf R)+V_{NN}(\mathbf R).
$$

Here $\hat H_e$ contains the electronic terms above, $\mathbf r$ denotes all electron coordinates and spins, $n$ labels an electronic state, $\psi_n$ is its wavefunction, $\epsilon_n$ its electronic eigenvalue, and $V_{NN}$ the last, nuclear-repulsion term. Some software includes $V_{NN}$ inside its reported “electronic total energy”; always inspect the output definition. The potential energy surface, or PES, is $E_n$ as a function of nuclear geometry.

The Born–Oppenheimer approximation separates electronic and nuclear motion. A single-state approximation writes the molecular wavefunction approximately as an electronic state times a nuclear wavefunction, neglecting couplings to other states. Replacing that nuclear wavefunction by classical particles is a **further** approximation. The derivation and limitations near degeneracies appear in [Rawlinson and Tronci, sections 1.1–1.2](https://arxiv.org/html/2005.10784).

For a smooth isolated surface, the ordinary classical force is $\mathbf F_A=-\nabla_AE_n$. An energy label is a surface height; a force label is a local slope. A force field can therefore describe bond breaking without explicitly carrying a bond graph, provided its surface is accurate through the breaking region. Conversely, matching equilibrium energies alone need not constrain the relevant slopes.

A single surface can fail when electronic states mix strongly, light excites the molecule or spin-changing processes become important. Avoid claiming that an arbitrary latent vector implements such processes: state populations, couplings, preparation and validation observables would need definitions.

> **In plain words.** A potential energy surface is a landscape that changes height as atoms move. Electrons determine its shape, while nuclei travel across it. Usually we assume the electrons settle into the appropriate arrangement quickly enough to redraw the landscape as needed. Near a crossing between electronic states, following only one landscape can miss the route the molecule actually takes.

## Reactions, stationary points and energy differences

A reaction connects distinguishable reactant and product regions through rearrangement of electronic density and nuclei. Bond labels are useful descriptions, but thresholds on distances are analysis choices, not terms in the fundamental Hamiltonian.

Let $\mathbf R_R,\mathbf R_P,\mathbf R_\ddagger$ denote reactant, product and transition-state geometries on the same declared surface. Then

$$
\Delta E=E(\mathbf R_P)-E(\mathbf R_R),\qquad
\Delta E^\ddagger=E(\mathbf R_\ddagger)-E(\mathbf R_R).
$$

These equations define electronic reaction energy and forward barrier, respectively. An elementary transition state is a first-order saddle: its gradient vanishes and its internal mass-weighted curvature has one negative direction. A vibrational analysis consequently reports one imaginary internal frequency. Numerical translation/rotation artefacts must be distinguished from that physical direction. Follow the downhill paths to confirm the intended reactants and products; a saddle alone does not establish a mechanism.

Zero-point energy adds nuclear vibrational ground-state contributions; thermal enthalpy and entropy introduce further terms. A free-energy barrier includes the accessible configurations and chosen standard state. [Psi4's thermochemistry documentation](https://psicode.org/psi4manual/master/thermo.html) distinguishes electronic totals from corrections and warns against mixing incompatible reference zeros. [Kinetics](04-reaction-kinetics-and-rare-events.md) explains why an electronic barrier cannot simply be inserted as a free-energy barrier in a rate expression.

For separated reactants, specify whether the reference is isolated fragments or an associated entrance complex. Both are meaningful; their barrier heights answer different questions. Keep composition and charge balanced before subtracting energies.

> **In plain words.** A reaction energy compares where a journey starts and ends. A barrier asks how high a pass must be crossed on the way. Warm molecules also have many possible ways to move and arrange themselves, so the effective difficulty of the journey is more than the height shown on a single cold map. Label the kind of map before quoting a barrier.

## Hydrogen exchange as a worked conceptual example

Label the atoms temporarily as $H_a+H_bH_c\rightarrow H_aH_b+H_c$. These labels track identity; all hydrogen atoms of the same isotope remain physically interchangeable. The system contains three electrons. Ground-state H has spin $S=1/2$ and ground-state H₂ has $S=0$, so their ground-state entrance channel has total $S=1/2$ and multiplicity $2S+1=2$: a doublet. This follows directly from spin addition and the [restricted versus unrestricted/open-shell definitions in Psi4](https://psicode.org/psi4manual/master/scf.html#spin-symmetry-treatment). An odd electron count by itself rules out a singlet but does not rule out every higher-spin excited state.

At the same isotope and ground-state asymptotes, this identity exchange has equal reactant and product energies. That symmetry does not imply a zero barrier. A collinear scan is a helpful teaching slice through the surface, not the full collision problem: collision orientation, impact parameter, rotational/vibrational state and isotope masses matter.

Classical trajectories on an accurate PES still omit nuclear tunnelling and quantised nuclear motion. Hydrogen is therefore a good test of surface construction and symmetry, but a demanding test of physical rates. The [author-hosted H + H₂ surface/scattering treatment](https://comp.chem.umn.edu/truhlar/docs/C6.pdf) is retrieved as a scanned PDF; no numerical barrier is adopted here because this research pass did not extract a reliable numerical protocol from it.

> **In plain words.** Hydrogen exchange is a partner swap between a lone atom and a pair. The starting and ending arrangements can cost the same while the swap still requires climbing a hill. There is an unpaired electron, so a calculation designed only for fully paired electrons is the wrong starting point. Light hydrogen nuclei also behave less like tiny billiard balls than classical simulations assume.

## What this implies for an NPA, and exercises

For a ground-state PES target, geometry and the declared electronic problem determine the desired energy. Different initial latent states must not create unexplained different energies for that same problem. A latent state might accelerate an iterative electronic approximation, represent a deliberately coarse-grained memory, or describe additional electronic preparation; these are different proposals requiring different data.

Separate element networks are compatible with physical forces if they contribute to a jointly trained invariant scalar,

$$
E_\theta(\mathbf R)=\sum_A e_{\theta_{Z_A}}(\mathcal D_A),\qquad
\mathbf F_A=-\nabla_A E_\theta.
$$

$\theta$ denotes all learned parameters, $e_{\theta_{Z_A}}$ an element-specific atomic energy network and $\mathcal D_A$ its environment descriptor. The gradient must include every contribution depending on atom $A$, including neighbours' outputs. The [Behler–Parrinello paper](https://aiichironakano.github.io/cs653/Behler-NNPES-PRL07.pdf) establishes the atomic-sum construction. Atomic terms are a representation, not uniquely observable atomic energies. Independent force agents lack this construction's guarantee.

**Exercises, with expected checks:**

- Write electron counts and possible ground-state entrance multiplicities for H + H₂ and H₂ + H₂. Check that the former is doublet and the latter can be singlet with both molecules in their ground states.
- Translate and rotate a geometry. Predict that its scalar energy stays fixed and force vectors rotate with it, assuming no external field.
- Draw a symmetric double-well curve. Mark equal endpoints and a nonzero intervening barrier; explain why reaction energy cannot identify reaction speed.
- For a proposed hidden state, write one observable that could distinguish two physical electronic preparations at identical coordinates. If none is specified, do not claim the state is electronic memory.

> **In plain words.** An NPA needs a clearly named physical job before its extra memory can be judged. Several specialist networks can cooperate safely when their answers build one shared energy landscape. They cannot each invent unrelated pushes and expect the whole system to behave consistently. The exercises ask whether you can identify the landscape, its symmetries and the information missing from a picture of atoms.

## Open questions

- Which electronic state and reference calculation will define the hydrogen surface?
- Is the initial project a ground-state classical-nuclei model, or does any claimed observable require quantum nuclei or multiple electronic states?
- What evidence would anchor a latent state to a physical electronic variable?

> **In plain words.** The next decision is which simplified version of nature the first model promises to reproduce. A small promise can be tested carefully. An undefined promise cannot be rescued by an attractive simulation.

## What would change this document

Explicit excited-state targets, heavy-element relativistic requirements or a quantum-nuclear rate benchmark would require extensions to the Hamiltonian and validation protocol. Demonstrated nonadiabatic data would also change the interpretation of state variables. There is no implementation or measured NPA chemistry result behind these recommendations.

> **In plain words.** This starting rulebook is suitable for an ordinary single electronic landscape. New physical ingredients require new rules and new evidence. They should be added because a defined question needs them.

## Sources

- Psi4 developers, *HF: Hartree–Fock Theory*, official manual. https://psicode.org/psi4manual/master/scf.html (retrieved 2026-11-07).
- Rawlinson and Tronci, *Regularized Born–Oppenheimer molecular dynamics*, 2020, full text. https://arxiv.org/html/2005.10784 (retrieved 2026-11-07).
- Psi4 developers, *Vibrational and Thermochemical Analysis*, official manual. https://psicode.org/psi4manual/master/thermo.html (retrieved 2026-11-07).
- Truhlar and Wyatt, *H + H₂: Potential-Energy Surfaces and Elastic and Inelastic Scattering*, author-hosted scan. https://comp.chem.umn.edu/truhlar/docs/C6.pdf (retrieved 2026-11-07; scanned numerical content not extracted).
- Behler and Parrinello, *Generalized Neural-Network Representation of High-Dimensional Potential-Energy Surfaces*, Physical Review Letters, 2007. https://aiichironakano.github.io/cs653/Behler-NNPES-PRL07.pdf (retrieved 2026-11-07).
