---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-electronic-structure-primer.md, 02-density-functional-theory.md]
---

# Wavefunction methods and honest reference error bars

A learned potential needs trustworthy targets, but “high-level reference” does not mean exact. This tutorial explains the hierarchy from Hartree–Fock to coupled cluster, how basis extrapolation and composite calculations work, and how to report uncertainty in the particular energy differences the NPA project would predict.

**Actionable takeaways**

- Treat a reference as a documented calculation with a domain of reliability, rather than an unquestionable number.
- Use matched settings and electronic states across reactants, transition states and products.
- Separate basis incompleteness, correlation truncation, geometry, numerical and physical-model errors.
- Use CCSD(T) cautiously where bonds are strongly stretched or multiple electronic configurations compete.
- Report sensitivity ranges unless there is evidence supporting a statistical confidence interval.

## Hartree–Fock: the reference determinant

Hartree–Fock (HF) minimises energy over single Slater determinants, antisymmetrised products of spin orbitals. Electrons experience an optimised mean field, with exact exchange within that determinant but without general correlated motion. The finite-basis orbital equation is

$$
\mathbf F\mathbf C=\mathbf S\mathbf C\boldsymbol\varepsilon.
$$

$\mathbf F$ is the density-dependent Fock matrix, $\mathbf C$ the orbital coefficients, $\mathbf S$ basis-overlap matrix and $\boldsymbol\varepsilon$ the diagonal orbital-energy matrix. Self-consistency is necessary because occupied orbitals determine the density that constructs $\mathbf F$. [Psi4's HF manual](https://psicode.org/psi4manual/master/scf.html) states the determinant, Hamiltonian and spin variants explicitly.

Restricted HF pairs opposite-spin electrons in the same spatial orbitals. Unrestricted HF permits different spatial orbitals for the spin components but can lose pure total-spin character; restricted open-shell HF treats unpaired electrons differently. Record the chosen reference and inspect $\langle\hat S^2\rangle$, the expected squared total spin, against the intended $S(S+1)$ in units with $\hbar=1$.

The variational principle bounds a properly optimised HF energy above the exact ground-state energy of the same Hamiltonian. It does not imply that a difference of HF energies bounds a reaction energy. Nor does it imply a monotonic accuracy hierarchy across unrelated approximations. For the doublet H + H₂ channel, a closed-shell restricted reference is not appropriate.

> **In plain words.** Hartree–Fock gives each electron an average view of the others while respecting the rules for exchanging identical electrons. Real electrons coordinate their movements more closely than that picture allows. A better total energy for each separate structure does not automatically mean a better difference between them. That difference is what a chemical barrier needs.

## MP2 and coupled cluster: what is added

Second-order Møller–Plesset perturbation theory (MP2) estimates a leading correlation correction to an HF reference. In a spin-orbital convention,

$$
E^{(2)}=\frac14\sum_{ijab}
\frac{|\langle ij\Vert ab\rangle|^2}
{\varepsilon_i+\varepsilon_j-\varepsilon_a-\varepsilon_b}.
$$

$i,j$ label occupied orbitals, $a,b$ virtual orbitals, $\varepsilon$ orbital energies, and $\langle ij\Vert ab\rangle$ antisymmetrised electron-repulsion integrals. The numerator measures coupling to a double excitation; the denominator measures its reference energy separation. Small denominators explain why a nominal correction may cease to be small. This is an explanatory derivation from perturbation theory, not a guarantee of accuracy in a stretched bond. The [official MP2 implementation documentation](https://psicode.org/psi4manual/master/dfmp2.html) describes density fitting and supported reference types.

Coupled cluster instead uses

$$
|\Psi\rangle=e^{\hat T}|\Phi_0\rangle,\qquad
\hat T=\hat T_1+\hat T_2+\cdots.
$$

$|\Phi_0\rangle$ is the reference determinant and $\hat T_n$ generates connected excitations of rank $n$. CCSD retains single and double excitation operators; the exponential also generates products describing disconnected higher excitations. CCSD(T) adds a perturbative estimate of connected triples. This construction gives size extensivity: for noninteracting copies, the calculated energy scales additively. It does not make the truncated method exact or generally variational. [Psi4's coupled-cluster theory](https://psicode.org/psi4manual/master/cc.html) gives this expansion and canonical leading costs $O(o^2v^4)$ for CCSD and $O(o^3v^4)$ for triples, with $o,v$ occupied and virtual orbital counts. These are asymptotic operation estimates, not runtime predictions.

Full configuration interaction is exact **within a specified finite orbital basis and Hamiltonian** when all allowed determinants are included. It is not a complete-basis or relativistically exact answer. Local-correlation and pair-truncation schemes reduce expense but introduce further thresholds that require checking for the reaction under study.

> **In plain words.** MP2 adds a first estimate of how electrons move together. Coupled cluster builds a richer pattern of coordinated rearrangements. These improvements work best when the starting electronic picture is already reasonable. If that starting picture is badly wrong, a correction designed to be small can become unreliable.

## Complete-basis extrapolation, derived

A complete-basis-set (CBS) limit removes orbital-basis incompleteness for a chosen electronic method. It does not remove that method's correlation error. Different convergence behaviour motivates extrapolating HF and correlation components separately; [Psi4's CBS manual](https://psicode.org/psi4manual/master/cbs.html) implements this separation and staged corrections.

For a correlation component, assume

$$
E_X=E_\infty+AX^{-p},\qquad
E_\infty=\frac{X^pE_X-Y^pE_Y}{X^p-Y^p}.
$$

$X,Y$ are cardinal numbers of a consistent basis family, $E_X,E_Y$ the correlation energies, $A$ an unknown coefficient, $p$ a chosen convergence exponent and $E_\infty$ the extrapolated limit. Multiply each first equation by its cardinal number to power $p$; subtract to eliminate $A$. The [documented Helgaker correlation scheme](https://psicode.org/psi4manual/master/cbs.html) uses an inverse-cubic model in its standard form. Small bases need not lie in the asymptotic regime, so a precise extrapolated value can still be wrong.

Do not mix basis families or extrapolate a total energy using an expression intended for correlation alone. Diffuse functions, core–valence bases and effective core potentials must be consistent across stages. Test the extrapolation by changing the pair or adding a larger basis where affordable. The difference is evidence of sensitivity, not a mathematically certified bound.

> **In plain words.** A finite basis is a limited vocabulary for describing electrons. Extrapolation guesses what the answer would be with an unlimited vocabulary by observing how it changes as the vocabulary grows. That guess needs a trustworthy pattern of convergence. It cannot repair a separate mistake in the underlying electronic theory.

## Composite references and difficult electronic structure

A composite energy combines a relatively affordable large-basis result with smaller-basis higher-level increments. A schematic definition is

$$
E_{comp}=E_{HF}^{CBS}+E_{corr,CCSD(T)}^{CBS}
+\Delta E_{higher}+\Delta E_{core}+\Delta E_{rel}+\Delta E_{other}.
$$

$E_{comp}$ is the assembled energy; the first two terms are extrapolated HF and correlation components; increments estimate higher connected excitations, core correlation, relativistic effects and any explicitly named remaining corrections. The equation is a bookkeeping template, not the exact definition of an established named protocol. Zero-point and thermal terms must be added separately when the target is a thermochemical quantity.

[Karton and colleagues' W4 paper](https://arxiv.org/html/physics/0608123) is a concrete primary example: its computational details and definition section specify high-excitation, core, relativistic and Born–Oppenheimer-related ingredients and discuss problematic convergence. Its main-group validation cannot be promoted into an accuracy promise for arbitrary metal precursors.

A single-reference warning panel should combine orbital occupations, excitation-amplitude diagnostics, spin contamination, the relative triples contribution and behaviour along a geometry scan. None is a universal pass/fail certificate. Disagreement between restricted and unrestricted descriptions may expose instability without identifying the exact answer. If several configurations are essential, request an appropriate multireference assessment or an exact small-system comparison; do not merely attach more decimal places to CCSD(T).

**Proposed project choice:** use small, chemically targeted high-level audits before spending a large label budget. Include strained geometries and transition regions, because the audit must match the model's intended operating domain.

> **In plain words.** A composite calculation is an itemised bill: a main estimate plus separately checked corrections. It is useful because the expensive parts can be calculated on smaller problems. Every item still has assumptions. A recipe verified for small main-group molecules is not automatically verified for every industrial precursor.

## Turning reference limitations into usable error bars

For a barrier $B=E_\ddagger-E_R$, statistical propagation would give

$$
\operatorname{Var}(B)=\operatorname{Var}(E_\ddagger)+\operatorname{Var}(E_R)
-2\operatorname{Cov}(E_\ddagger,E_R).
$$

$E_\ddagger,E_R$ are transition and reactant energies; variance and covariance describe a specified uncertainty model. The minus covariance term explains cancellation of correlated errors. Electronic-structure bias is usually not a sample of independent random noise; this identity alone does not supply the needed probability model.

Use an **error budget** instead: report changes from basis enlargement, alternative extrapolation, stronger correlation treatment, reference choice, tighter numerical settings and alternative geometries. State which contributions are estimated and which remain unassessed. Do not add their magnitudes in quadrature unless independence and statistical interpretation are justified. A conservative envelope can be labelled a sensitivity range. Geometry optimisation at a lower level followed by a high-level single point must be written explicitly as a mixed protocol.

Model uncertainty, reference-method discrepancy and sampling uncertainty are different. An ensemble of neural networks trained on the same biased labels need not reveal label bias. Conversely, matching imperfect labels does not logically forbid a model from being closer to exact values by accident or useful regularisation; it provides no evidence of systematic improvement without independent references.

> **In plain words.** A reference number has several ways to be wrong, and some errors cancel when two numbers are subtracted. A spread from changing calculation settings tells you what was tested. It is not automatically the same as a statistical confidence interval. Keep the model's uncertainty separate from uncertainty in its teacher.

## Exercises and a reference record

For every proposed label, preserve geometry identifier, composition, charge, multiplicity, method, reference determinant, basis, frozen-core choice, relativistic treatment, auxiliary basis, numerical tolerances, program version and whether the number contains nuclear repulsion or thermal corrections.

**Exercise:** derive the CBS expression by eliminating $A$. Then choose symbolic errors $\delta_R,\delta_\ddagger$ and show that the barrier error is $\delta_\ddagger-\delta_R$. Construct equal errors that cancel and opposite-sign errors that amplify. Finally, design a calculation matrix that changes basis and correlation level independently at the same geometries. Expected outcome: each sensitivity can be named; changing both simultaneously cannot identify which caused the observed shift. These are proposed learning tasks, not completed calculations.

> **In plain words.** A good reference record lets another person rebuild both the answer and its limitations. The exercises show why shared mistakes can disappear in a difference while different mistakes grow. That is why accuracy must be checked on the actual barrier or reaction energy, not inferred from impressive total energies.

## Open questions

- Which reference methods are reliable along the selected hydrogen and precursor reaction paths?
- What high-level gradient coverage exists, rather than energy-only coverage?
- How much of a label audit can the actual compute budget support?

> **In plain words.** The best reference is the one whose weaknesses are understood for the chosen problem. Cost and missing derivatives may restrict that choice. Those restrictions should appear beside the labels.

## What would change this document

A selected reaction panel, multireference diagnostics or a validated composite protocol for the intended elements would make the recommendations more specific. No numerical reference uncertainty has been assigned without those calculations.

> **In plain words.** Real calculations can replace a general checklist with measured sensitivities. Until then, an honest list of unknown errors is more useful than an invented error bar. The project should budget for that evidence.

## Sources

- Psi4 developers, *HF: Hartree–Fock Theory*. https://psicode.org/psi4manual/master/scf.html (retrieved 2026-11-07).
- Psi4 developers, *DF-MP2*. https://psicode.org/psi4manual/master/dfmp2.html (retrieved 2026-11-07).
- Crawford / Psi4 developers, *CC: Coupled Cluster Theory*. https://psicode.org/psi4manual/master/cc.html (retrieved 2026-11-07).
- Psi4 developers, *Complete Basis Set*. https://psicode.org/psi4manual/master/cbs.html (retrieved 2026-11-07).
- Karton, Rabinovich, Martin and Ruscic, *W4 theory for computational thermochemistry*, Journal of Chemical Physics, 2006, full text. https://arxiv.org/html/physics/0608123 (retrieved 2026-11-07).
