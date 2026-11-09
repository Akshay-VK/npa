---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-electronic-structure-primer.md]
---

# Density functional theory: the approximation inside the labels

Density functional theory (DFT) is likely to supply many training labels and is the object the challenge explicitly asks entrants to improve. Understanding what its energy depends on, how its equations are solved and where its errors enter prevents confusing a fast fitted molecular potential with a new exchange–correlation functional.

**Actionable takeaways**

- Record the full functional, basis, quadrature, spin treatment, dispersion and convergence settings with every DFT label.
- Distinguish a molecular potential $E(\mathbf R)$ from a density functional $E_{xc}[\rho]$; their inputs and deployment obligations differ.
- Converge numerical settings before attributing an error to the functional.
- Examine bond stretching, charge transfer and weak binding separately; a favourable average can hide the failure relevant to a reaction.
- Treat temperature as a sampling variable for ordinary ground-state PES work, rather than an unexplained correction to the electronic Hamiltonian.

## Density and the Hohenberg–Kohn result

The electron density $\rho(\mathbf r)$ is the expected number of electrons per spatial volume near $\mathbf r$. It obeys $\int\rho(\mathbf r)d\mathbf r=N_e$, where $N_e$ is electron count. Unlike the many-electron wavefunction, it is a function of a single spatial position. A **functional** maps an entire function to a number.

For a fixed electron interaction, the Hohenberg–Kohn framework establishes the ground-state density as the central variable and a variational energy principle. In the usual nondegenerate formulation, the density determines the external potential up to an additive constant. Degeneracy and representability require careful extensions; the result does not state that every arbitrary nonnegative function corresponds to a unique ordinary Kohn–Sham ground state. Kohn describes the density variational construction in his [first-person account](https://www.nobelprize.org/prizes/chemistry/1998/kohn/biographical/). The original 1964 PDF timed out during this research pass, so no claim depends on having read that PDF.

A useful formulation is

$$
E_0=\min_{\rho\rightarrow N_e}\left\{F[\rho]+\int v_{ext}(\mathbf r)\rho(\mathbf r)d\mathbf r\right\}+V_{NN}.
$$

$E_0$ is the ground-state total energy, $F$ the universal interacting electronic kinetic-plus-repulsion functional, $v_{ext}$ the electron potential due to fixed nuclei (and declared external fields), and $V_{NN}$ nuclear repulsion. The arrow denotes admissible densities with the stated electron count. “Universal” means independence from the chosen external potential, not that an existing approximation has been validated on all chemistry.

> **In plain words.** Electron density is a map of where electrons are likely to be found. DFT says a ground-state energy can be obtained from the right map without retaining the whole many-electron wavefunction. That is a profound simplification, but it does not hand us the exact recipe for calculating the energy. Approximate recipes remain the practical difficulty.

## Deriving the Kohn–Sham working problem

Kohn–Sham theory introduces auxiliary noninteracting orbitals to represent the density. In atomic units,

$$
E[\rho]=T_s[\rho]+\int v_{ext}\rho\,d\mathbf r+E_H[\rho]+E_{xc}[\rho]+V_{NN},
\quad
E_H=\frac12\iint\frac{\rho(\mathbf r)\rho(\mathbf r')}{|\mathbf r-\mathbf r'|}d\mathbf r\,d\mathbf r'.
$$

$T_s$ is the noninteracting orbital kinetic energy, $E_H$ classical Coulomb repulsion and $E_{xc}$ everything missing from those terms, including the interacting-minus-noninteracting kinetic contribution. The factor of one half avoids counting the same density pair twice. The [Psi4 DFT theory section](https://psicode.org/psi4manual/master/dft.html) gives the corresponding finite-basis implementation.

Minimising with orthonormal orbitals gives, for a local multiplicative Kohn–Sham potential,

$$
\left[-\tfrac12\nabla^2+v_{ext}+v_H+v_{xc}\right]\phi_i=\varepsilon_i\phi_i,
\qquad \rho=\sum_i f_i|\phi_i|^2.
$$

$\phi_i$ is an orbital, $\varepsilon_i$ its eigenvalue, $f_i$ its occupation, $v_H=\delta E_H/\delta\rho$ and $v_{xc}=\delta E_{xc}/\delta\rho$ functional derivatives. Spin-polarised calculations use separate spin densities. Orbital-dependent hybrids generally use a generalised Kohn–Sham operator that is not simply the local $v_{xc}$ displayed here.

The equations depend on the density they themselves produce. Self-consistent field (SCF) iteration guesses a density, constructs the effective operator, solves for orbitals, rebuilds the density and repeats until residual and energy criteria are satisfied. Convergence is a numerical condition; it does not prove that the correct electronic state or global minimum was found. Check stability and alternative guesses where chemistry is difficult.

A learned XC energy must supply consistent derivatives and work inside this feedback loop. Fitting accurate molecular energies at fixed geometries does not establish derivative quality, density quality or SCF robustness. That is why an atomistic NPA energy model and a challenge-compatible functional are different deliverables.

> **In plain words.** Kohn–Sham theory solves an easier electron problem and puts the missing physics into a correction. The answer changes the correction, so the calculation repeats until the input and output agree. A learned correction must behave sensibly during those repetitions. Giving good final answers to a list of molecules is only part of that job.

## Jacob's ladder and the cost it adds

The ladder classifies ingredients, rather than guaranteeing an accuracy ranking. Local density approximations use density at a point; generalised gradient approximations also use its spatial variation; meta-GGAs add ingredients such as orbital kinetic-energy density; hybrids incorporate nonlocal exact exchange; double hybrids also add perturbative correlation. See [Psi4's functional definitions and custom-functional interface](https://psicode.org/psi4manual/master/dft.html) for actual ingredients, which matter more than a nickname.

Moving upward can address missing information but adds computational work and sometimes new failure modes. Exact exchange requires nonlocal orbital integrals. Perturbative correlation inherits sensitivity to small orbital-energy gaps. Range separation divides exchange by interelectronic distance; it is not the same operation as increasing an atom-neighbour cutoff in a fitted potential.

**Proposed project practice:** select a modest, dispersion-aware baseline and a more expensive comparison only after checking element, charge and spin support. Record the exact implementation and version. Do not pick a functional merely because it occupies a higher rung or tops an unrelated aggregate benchmark. Detailed comparative selection belongs in [the functional landscape](../02-prior-art/02-functional-zoo-and-jacobs-ladder.md), rather than duplicating performance tables here.

> **In plain words.** The ladder is a list of extra information that an energy recipe is allowed to use. More information can help, but it can also cost more and be used badly. Choosing a method is like choosing a measuring instrument: suitability for the sample matters more than the price tag. Test the reaction types that the project actually needs.

## Why reaction energies and barriers go wrong

**Delocalisation error:** many approximations favour fractional electron sharing between distant fragments. For adjacent integer electron counts $N$ and $N+1$, the exact ensemble energy between them is linear:

$$
E(N+\alpha)=(1-\alpha)E(N)+\alpha E(N+1),\qquad 0\leq\alpha\leq1.
$$

$\alpha$ is the fractional ensemble weight. Curvature away from this line can favour incorrect charge distributions. [Yang, Mori-Sánchez and Cohen](https://arxiv.org/html/1305.5194) derive fractional-charge/spin extensions rather than treating these as merely numerical SCF problems.

**Static correlation error:** when several electronic configurations become important, a simple approximate description may fail, especially during bond dissociation. [Cohen, Mori-Sánchez and Yang's full paper](https://arxiv.org/html/0805.1724) connects fractional-spin constancy violations with the dissociation problem. Adding exact exchange does not automatically solve this.

**Dispersion:** long-range correlation contributes to noncovalent binding and precursor association. Specify whether it comes from a fitted correction or a nonlocal functional, and avoid adding it twice. **Density error:** the approximate self-consistent density can contribute separately from the functional's error evaluated on a better density. Neither a large basis nor tighter SCF convergence repairs all these approximations.

Barrier errors often reflect unequal stabilisation of reactants and a more stretched or charge-redistributed transition region. The direction and magnitude are system dependent. Do not convert a general tendency into a guaranteed correction to every barrier.

> **In plain words.** A reaction passes through electron arrangements unlike those of a comfortable stable molecule. A recipe may spread electrons too widely, mishandle a breaking bond or miss weak attractions between fragments. Tightening numerical settings makes that recipe more precisely evaluated. It does not make the recipe exact.

## Basis sets, grids, label provenance and exercises

A finite basis expands orbitals in specified functions. Larger and more flexible bases reduce representation error, while diffuse functions help describe extended densities and polarisation functions allow angular flexibility. A numerical quadrature grid evaluates XC integrals; it is a separate approximation. Effective core potentials replace selected core electrons and change what must be recorded. Small-basis binding calculations can also benefit artificially from a partner's basis functions; this is basis-set superposition error.

For forces, all coordinate dependence must be differentiated. In an atom-centred basis, basis motion contributes Pulay terms. The simple expectation of the explicit Hamiltonian derivative alone is generally insufficient. Prefer documented analytic gradients or carefully converged finite differences.

**Exercises:** choose a small declared molecule and fixed geometry; compare two basis sizes at fixed functional, then two grids at fixed basis. Record changes separately, including forces. This is a convergence exercise, not a benchmark claim. Next stretch a bond and inspect SCF state changes and spin diagnostics. Finally, write two input contracts: one for a geometry-to-energy model and one for an XC functional. The latter must describe density/orbital ingredients, derivatives and the SCF interface. Explain why the first contract cannot substitute for the second.

> **In plain words.** A basis is the set of shapes used to describe the electrons; a grid is how the calculation adds up contributions across space. Both can be too coarse in different ways. Change one at a time to learn which is responsible. Keeping the full settings is what makes a numerical label reusable evidence.

## Open questions

- Which level of theory supplies the initial reactive labels, and which higher-level cases will audit it?
- Which charge and spin regimes are necessary before adding heavier precursors?
- Is any future learned functional evaluated self-consistently, or only as a correction on fixed densities?

> **In plain words.** “DFT data” is an incomplete specification. The project still needs to name the recipe and the difficult examples used to test it. Otherwise model error and reference error will remain mixed together.

## What would change this document

An accepted functional implementation, explicit finite-electronic-temperature target or evidence that density error dominates the selected reactions would alter the recommendations. No project-specific functional ranking or accuracy result has been measured here.

> **In plain words.** The right advice depends on the physical question and the actual calculation. A measured failure can justify changing the recipe. A fashionable method name alone cannot.

## Sources

- Kohn, autobiographical account of the density variational principle, Nobel Prize website. https://www.nobelprize.org/prizes/chemistry/1998/kohn/biographical/ (retrieved 2026-11-07).
- Psi4 developers, *DFT: Density Functional Theory*, official manual. https://psicode.org/psi4manual/master/dft.html (retrieved 2026-11-07).
- Yang, Mori-Sánchez and Cohen, *Extension of many-electron theory and approximate density functionals to fractional charges and fractional spins*, 2013, full text. https://arxiv.org/html/1305.5194 (retrieved 2026-11-07).
- Cohen, Mori-Sánchez and Yang, *Fractional Spins and Static Correlation Error in Density Functional Theory*, 2008, full text. https://arxiv.org/html/0805.1724 (retrieved 2026-11-07).
