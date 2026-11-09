---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: []
---

# Long-range interactions, charge and boundaries

A finite particle neighbourhood is a computational choice, not a statement that all relevant chemistry is short-range. This document defines the extra physics and numerical contracts required when charge transfer, separated fragments or periodic systems enter the deployment domain.

**Key takeaways**

- State isolated, periodic and slab electrostatics explicitly.
- Differentiate charge-dependent energy consistently.
- Test separated fragments and total-charge conservation.

## Locality and a useful counterexample

Imagine two local atomic environments that are identical within the cutoff while a charged fragment is moved far outside it. A strictly local descriptor cannot distinguish them, although their electrostatic energies and forces may differ. Adding more training examples cannot resolve an input representation that maps physically different cases to the same features. More message-passing layers extend a finite receptive field; they do not automatically supply correct asymptotic interactions.

A proposed decomposition is a learned short-range energy plus explicitly defined electrostatics and dispersion. Train the residual appropriate to that decomposition to avoid counting interactions twice. If starting from a pretrained total-energy model, do not add a Coulomb term without recalibration. Compare the local-only and corrected forms on fragment-separation scans, charge states and binding curves.

> **In plain words.** Two people may see identical nearby surroundings while one feels a pull from something far away. A short-sighted model cannot tell the difference. You need a way to include the distant influence, not merely more examples of the same incomplete view.

## Charge equilibration and derivatives

An illustrative proposed charge model minimises
$$E_q(q;R)=\sum_i\chi_i(R)q_i+\tfrac12 q^T J(R)q,\qquad \sum_iq_i=Q.$$
Here $q_i$ are model charges, $Q$ specified total charge, $\chi_i$ learned electronegativity-like coefficients and $J$ a hardness/interaction matrix. A stable constrained solve requires suitable definiteness on the charge-conserving subspace, an explicit treatment of close contacts and a residual tolerance. Fourth-generation potentials provide an established example of combining charge equilibration with local atomic energies [QEQ]. This equation is a design illustration, not a selected implementation.

If the reported total energy contains further terms depending on $q$, stationarity of only a partial charge objective does not necessarily remove every charge-response term from the total derivative. Differentiate the actual computational objective, including geometry dependence of coefficients and all relevant solver responses. Check forces by finite differences through the same convergence procedure used in production.

Imposing $\sum_iq_i=Q$ fixes a necessary total constraint but does not establish correct fragment charge transfer. At dissociation, some charge models spuriously spread fractional charge. Probe both identical and different fragments. Label supervision must identify the population-analysis convention; partial charges are not uniquely observable.

> **In plain words.** Give the atoms a fixed total amount of electrical charge to share. A rule for sharing it can still make the wrong choice, especially when fragments move apart. Also, if the sharing changes when atoms move, the force calculation must account for that change.

## Boundary conditions and dispersion

For an isolated molecule use an isolated electrostatic convention. For periodic matter the interaction includes periodic images; Ewald or particle-mesh methods require consistent short-range and reciprocal-space pieces and stated boundary assumptions [LAM]. A charged periodic cell also needs a declared background and correction convention. Slabs require attention to unwanted interactions across the vacuum direction. Do not use a periodic setting merely because the input format accepts a cell.

Dispersion has long-range contributions and short-range damping. Specify whether the label functional already includes a dispersion correction. Damping, learned residuals and any explicit correction must be treated together. A simple pair dispersion correction is a modelling approximation, not universally adequate for metals, screening or many-body environments.

> **In plain words.** Copying a molecule endlessly in every direction creates a different electrical problem from one molecule alone in space. A flat surface is different again. Long-distance attractions also need a clear accounting rule so they are not included twice.

## When to add complexity

Begin with a deliberately bounded neutral molecular task and quantify locality errors before adding charge machinery. Promote the long-range extension only if separation curves or charge-state tests show a consequential failure that the extension repairs. Track solver iterations and communication in the cost model. Finite-cutoff inference may scale approximately with atom count at fixed density, while global solves can change that scaling substantially. **Recommendation (inference):** use an established electrostatics implementation for the first periodic extension; do not simultaneously invent charge transfer, electrostatic summation and particle kernels.

> **In plain words.** First show which distant effect is missing and how much it matters. Then add one repair and measure its cost. Rebuilding every part of the electrical system at once makes faults hard to locate.

## Open questions

- Is the first chemistry task isolated and neutral?
- Which charge convention and electrostatic boundary are compatible with the labels?

> **In plain words.** These are choices that the current evidence does not settle. Write down the answer before spending money on an experiment that depends on it. An empty result is better than an invented answer.

## What would change this document

- Verified failures on charge-transfer or fragment-separation tests.
- A periodic or surface deployment requirement.

> **In plain words.** Treat this document like a map made before the expedition. New measurements can reveal a better route. Record what changed and why when that happens.

## Sources

- [Ko et al., fourth-generation neural potentials, full paper](https://arxiv.org/html/2009.06484) (retrieved 2026-11-07).
- [LAMMPS long-range solver documentation](https://docs.lammps.org/kspace_style.html) (retrieved 2026-11-07).
