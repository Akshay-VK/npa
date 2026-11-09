---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-landscape-and-taxonomy.md, 02-functional-zoo-and-jacobs-ladder.md]
---

# Learned exchange–correlation functionals

This is the most direct existing answer to the Discovered Materials challenge,
and therefore the project's most important neighbour. Two models matter: DM21
(DeepMind, 2021), which proved the concept and then stalled, and Skala
(Microsoft, 2025–2026), which is the current state of the art and is
explicitly designed to be systematically improvable. Reading them carefully
tells you what a learned functional actually requires — and why the NPA idea
is adjacent to, but not the same as, this line of work.

**Bottom line**

- A learned functional keeps the Kohn–Sham machinery and replaces only the
  unknown $E_{xc}[\rho]$. It is a component swap, not a new simulator.
- DM21 reached 3.97 kcal/mol WTMAD-2 but never saw routine use: it is a local
  range-separated hybrid, more expensive than global hybrids in practice, and
  it does not extrapolate to transition metals.
- Skala reaches **2.80 kcal/mol WTMAD-2** with **385,217 parameters**, at
  semi-local asymptotic cost. That is better than every hybrid on the same
  evaluation, including ωB97M-V at 3.23.
- Skala's key architectural move is exchanging information between integration
  grid points and atom-centred coarse points. This is structurally the same
  idea as particle perception — which makes the "grid points as particles"
  extension in the source note much more credible than it first appears.
- The binding constraint on this whole field is **high-accuracy training
  data**, not architecture. Skala uses ~400,000 CCSD(T)/CBS-quality energy
  differences. That is the moat.

## What "learned functional" means precisely

Kohn–Sham DFT writes the total energy as

$$
E[\rho] = T_s[\rho] + V_{ne}[\rho] + J[\rho] + E_{xc}[\rho],
$$

where the first three terms are known and $E_{xc}$ is not. Every practical
functional is an approximation to the last term. A learned functional replaces
the human-designed algebraic form of $E_{xc}$ with a neural network, while
leaving the SCF loop, the basis set, and the rest of the energy expression
untouched.

Two consequences follow immediately, and they are easy to forget:

1. **The output is an energy density on a grid**, integrated to give a scalar.
   Whatever the network does locally, the final object is $\int f(\mathbf{r})\,d\mathbf{r}$.
2. **The functional is evaluated inside a self-consistent loop**, so its errors
   change the density, which changes the functional's input, which changes the
   energy. Training on fixed densities is not the same as deploying on
   self-consistent ones.

The second point is the one that kills naive approaches. It is also the reason
Skala needs a two-stage training protocol.

> **In plain words.** A functional is one missing piece in an otherwise
> complete recipe for electronic energy. Learning it means learning that piece
> from examples. The catch is that the recipe is circular: the piece's output
> changes the input it is fed next time round, so you cannot just fit it once
> and walk away.

## DM21 — the proof of concept, and its ceiling

Kirkpatrick et al., *Pushing the frontiers of density functionals by solving
the fractional electron problem*, Science 374, 1385 (2021),
[DOI 10.1126/science.abj6511](https://www.science.org/doi/10.1126/science.abj6511).

**The idea.** Most density functionals fail badly on *fractional* electron
number and fractional spin — situations that arise when a molecule is stretched
towards dissociation, or when two fragments share an electron. A functional
that is wrong there produces delocalisation error, which is the root of many
reaction-barrier failures. DM21 was trained on artificial systems with
fractional charges and spins, forcing it to respect the piecewise-linearity
behaviour that the exact functional must have.

**The result.** State-of-the-art accuracy on several benchmarks at the time,
including systems specifically chosen to expose delocalisation error —
hydrogen chains, charged DNA base pairs, diradical transition states.

**Why it did not take over.** Three independent reasons, all documented:

1. **Cost.** DM21 is a *local range-separated hybrid*. Bystrom and Kozinsky
   describe it as "computationally expensive (even more so than global hybrid
   DFT) and not widely [used]"
   ([Phys. Rev. B 110, 075130, 2024](https://link.aps.org/doi/10.1103/PhysRevB.110.075130)).
   The whole point of a learned functional is to beat the accuracy–cost
   frontier; DM21 moved up the accuracy axis and the cost axis together.
2. **Coverage.** Its training set did not include heavy elements, and its
   developers cautioned against applying it beyond krypton
   ([Brémond et al., 2025](https://pubs.rsc.org/cp/article/28/6/3779/1247930/Contemporary-DFT-learning-from-traditional-and)).
   Zhao et al. showed it "does not extrapolate to transition metal chemistry"
   ([ChemRxiv, 2024](https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2024-6bxhz)).
   Since the ALD/CVD benchmark is precisely precursor chemistry, often with
   metals, this is directly relevant.
3. **Reproducibility and integration.** A functional that requires a bespoke
   implementation inside each quantum chemistry code, and whose results are
   hard to reproduce across codes, does not get adopted no matter how good its
   benchmark numbers are.

**The lesson for this project.** Benchmark accuracy alone does not create
adoption. Cost, coverage, and integration are co-equal requirements. Any
"we beat X on Y" claim must be accompanied by "and it runs in Z".

> **In plain words.** DM21 solved a famous hard problem and then nobody used
> it, because it was slower than what it replaced and only worked for lighter
> elements. Being right on a benchmark is not the same as being useful.

## Skala — the current state of the art

Luise et al., *Accurate and scalable exchange–correlation with deep learning*,
[arXiv:2506.14665v6](https://arxiv.org/abs/2506.14665) (retrieved 2026-11-07);
code at [github.com/microsoft/skala](https://github.com/microsoft/skala) under
MIT.

### Architecture

Skala builds in only minimal exact constraints and gains accuracy by learning
non-locality. Its form is

$$
E_{xc}^{\theta}[\rho]
= -\frac{3}{4}\left(\frac{6}{\pi}\right)^{1/3}
\int \left(\rho^{(\uparrow)4/3} + \rho^{(\downarrow)4/3}\right)
f_{\theta}\big[\mathbf{x}[\rho]\big](\mathbf{r})\,d\mathbf{r},
$$

where $f_\theta$ is a bounded enhancement factor and
$\mathbf{x}[\rho](\mathbf{r})$ are standard meta-GGA features at each
integration point: spin densities, density-gradient norms, and kinetic energy
density.

The pipeline at each grid point is:

1. **Spin-order-invariant features** from the meta-GGA inputs.
2. **Point-wise local processing** (an MLP).
3. **Non-local mixing**: each grid point exchanges information with its atom's
   *coarse point* — a representative point on a coarser, atom-centred grid.
4. **Combine and predict** the enhancement factor.
5. **Numerical integration** over the grid.

Total: **385,217 parameters**, of which 331,265 are in the local branch. The
non-local branch is deliberately lightweight so that asymptotic cost stays at
semi-local DFT, $O(N^3)$.

### The ablation that matters

Training identical models with and without the non-local branch, five seeds
each, evaluated on Diet GMTKN55: the non-local branch **reduces WTMAD-2 by
about 50%** (Skala §3.1, Fig. 2a). That is the single most important number in
the paper for this project, because it says the expensive part is doing real
work, and the work it is doing is *communication between points*.

Skala also reports an "effective non-local exchange" of 53.7% against a 60%
reference, and notes that its SN$_2$ barrier errors are roughly 2.5× smaller
than the best meta-GGAs.

### Training data

- **~395,000 energy differences** from the MSR-ACC collection, labelled with
  the W1-F12 and W1w thermochemical protocols, i.e. CCSD(T)/CBS quality.
- **~120,000** of these are total atomization energies, the largest component.
- Plus **~80,000** energy differences from public datasets of comparable
  accuracy.
- After overlap removal and holdout reservation: **~400,000** energy
  differences for Skala-1.1.
- Overlap with GMTKN55 and W4-17 is removed at the level of **molecular
  graphs**, not individual geometries — a much stronger guarantee than
  random splits.

The paper explicitly says the model was trained with a **fixed D3 dispersion
correction** and does not yet learn dispersion. This matters when comparing to
leaderboard numbers.

### Results

| Functional | Rung | WTMAD-2 (kcal/mol) | Notes |
|---|---|---|---|
| revPBE | GGA | 8.35 | D3(BJ) |
| r²SCAN | meta-GGA | 7.25 | D3(BJ) |
| B97M-V | meta-GGA | 5.56 | D3(BJ) |
| B3LYP | hybrid | 6.38 | D3(BJ) |
| M06-2X | hybrid | 4.83 | D3(0) |
| ωB97X-V | range-separated hybrid | 3.96 | D3(BJ) |
| ωB97M-V | range-separated hybrid | 3.23 | D3(BJ) |
| **Skala-1.1** | learned, semi-local cost | **2.80** | D3(BJ) |

All from Skala Table 1 and §3. Note the protocol: **all functionals carry a
dispersion correction**, which is *not* how the challenge's provisional
leaderboard is evaluated. See
[GMTKN55 and benchmark mechanics](04-gmtkn55-and-benchmark-mechanics.md) for why
this makes the two tables non-comparable.

Skala is best on 32 of 55 subsets. On W4-17 it reaches MAE 0.92 kcal/mol on the
183 single-reference reactions (1.23 overall, including multi-reference cases
it was not trained on).

### Caveats the paper states, and one it does not

Stated: slightly less smooth behaviour than traditional functionals; SCF
convergence and grid-size convergence are acceptable but not identical to
hand-designed functionals; dispersion is not learned; training data is
single-reference.

Not stated as prominently: Skala's training set is built from W1-F12/W1w
protocols, which are themselves CCSD(T)-based. So Skala's ceiling is
CCSD(T)/CBS accuracy *for single-reference systems*. Multi-reference chemistry
— bond breaking in stretched systems, some transition-metal complexes — is
outside its demonstrated domain. The paper's own multi-reference results
(Extended Data §E.1) show this is not solved.

> **In plain words.** Skala works by letting points on the calculation grid
> talk to a compressed representative point for each atom. That conversation
> halves the error. Everything else is a small network and a very large pile of
> extremely expensive reference data.

## The structural insight: Skala is a particle-message-passing model in disguise

This is the part that changes the project's strategic picture.

The source note's §11 speculates that "an NPA-like architecture where the
particles are grid points carrying density features could be an interesting way
to produce an exchange–correlation energy." At the time of writing it was a
hypothesis. Skala's methods section shows the hypothesis is substantially
correct: the winning ingredient is *learned exchange of information between
spatial points*, with atom-centred coarse points as the communication hubs.

The differences from a literal NPA are important:

| Skala | NPA |
|---|---|
| Points are fixed integration-grid points | Particles move |
| Communication is grid point ↔ atom coarse point | Particle ↔ neighbours within $\epsilon$ |
| Output is an enhancement factor, integrated | Output is a state/position increment |
| Cost target is $O(N^3)$, same as semi-local DFT | Cost target is linear in particles |
| Trained on energy differences inside an SCF loop | Trained on rendered endpoints |

So the correct reading is not "NPA could produce a functional" but "the
functional that works already uses the NPA *idea* (local points exchanging
learned messages), implemented in the form that DFT can actually consume."

**Strategic consequence.** If the project wants a challenge-shaped artefact, it
does not need to build NPA-for-grid-points from scratch. It needs to answer a
narrower question: *does persistent per-point state, or a different
communication topology, improve on Skala's coarse-point scheme at equal cost?*
That is a much more tractable and much more credible research question than
"replace DFT with an automaton".

> **In plain words.** The best existing learned functional already works by
> letting points on the grid pass messages to each other. That is the same
> trick as the particle automaton. So the gap between our idea and the
> competition is smaller than it looked — but the competition got there first,
> and got the plumbing right.

## Why learned functionals still have not taken over

A short, honest list, because it constrains what this project can promise:

1. **Data.** 400,000 CCSD(T)/CBS-quality energy differences is a
   multi-year, multi-expert effort. There is no public dataset of that quality
   at that scale. Skala's moat is MSR-ACC.
2. **Integration.** A new functional must be implemented in PySCF, ORCA,
   Gaussian, Turbomole, CP2K, and the rest before anyone can use it. Each
   implementation must agree to numerical precision.
3. **Trust.** A functional that is a neural network is harder to reason about
   than one with a closed form. When it fails, you cannot inspect the algebra.
4. **Smoothness.** SCF convergence depends on the functional's derivatives
   being well-behaved. Neural networks are only as smooth as their activations
   and training allow. Skala reports this is "slightly less smooth" and
   acceptable; that is an empirical result, not a guarantee.
5. **Benchmark culture.** The field has hundreds of functionals and a long
   history of overfitting to GMTKN55. A new entry is assumed guilty until
   proven innocent on held-out chemistry.

*(inference)* The fifth point is the most under-appreciated. Any learned
functional evaluated on GMTKN55 will be suspected of having seen it. Skala's
molecular-graph-level overlap removal is the right response, and any project
claim in this space must do the same.

> **In plain words.** Even a better functional does not spread by being better.
> It spreads when it is installed everywhere, trusted, and fast enough that
> people stop thinking about it. That takes years.

## What this means for the NPA project

1. **Do not compete on functional accuracy.** Skala has a 400k-point
   CCSD(T) dataset and a team. A small project cannot match it.
2. **Do compete on architecture insight.** The non-local mixing ablation is a
   clean, reproducible experiment. Asking whether a *different* mixing
   topology helps — persistent state, learned adjacency, higher body order — is
   a legitimate contribution at a fraction of the cost, because it can be
   tested on a small dataset.
3. **Borrow the evaluation discipline.** Molecular-graph-level splits, fixed
   dispersion, reported SCF convergence. These are cheap to adopt and
   expensive to omit.
4. **Treat the "grid points as particles" extension as a v2, not a v0.** It
   requires a DFT code you can modify and a data pipeline you do not have yet.

> **In plain words.** We cannot out-data them, so we should not try. We can
> out-ask them: does the way points talk to each other matter, and can memory
> help? That is a small, sharp question with a cheap experiment behind it.

## Open questions

- Does persistent per-point state help Skala's architecture, or does the SCF
  loop make state redundant (the density already encodes the history)?
- Could the coarse-point scheme be replaced by a learned $k$-nearest-neighbour
  graph without losing the $O(N^3)$ guarantee?
- How much of Skala's gain survives when the training set is reduced to
  10,000 points? This is the key question for a small team.
- Is DM21's failure primarily cost, coverage, or integration? The literature
  suggests all three, but a controlled comparison does not exist.

## What would change this document

- A public release of MSR-ACC, which would collapse the data moat and make
  this line of work accessible to small teams.
- A learned functional that beats Skala at lower cost, which would reset the
  baseline.
- Evidence that persistent state is incompatible with SCF convergence, which
  would rule out the hybrid for the functional application.

## Sources

1. Luise et al., *Accurate and scalable exchange–correlation with deep
   learning* (Skala), arXiv:2506.14665v6.
   <https://arxiv.org/abs/2506.14665> (retrieved 2026-11-07). Architecture
   §2.2, training §2.1 and §2.3, ablations §3.1, Table 1.
2. Kirkpatrick et al., *Pushing the frontiers of density functionals by solving
   the fractional electron problem*, Science 374, 1385 (2021).
   <https://www.science.org/doi/10.1126/science.abj6511> (retrieved
   2026-11-07).
3. Bystrom and Kozinsky, *Nonlocal machine-learned exchange functional for
   molecules and solids*, Phys. Rev. B 110, 075130 (2024).
   <https://link.aps.org/doi/10.1103/PhysRevB.110.075130> (retrieved
   2026-11-07).
4. Zhao et al., *Deep Mind 21 functional does not extrapolate to transition
   metal chemistry*, ChemRxiv (2024).
   <https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2024-6bxhz> (retrieved
   2026-11-07).
5. Brémond et al., *Contemporary DFT: learning from traditional and recent
   trends*, Phys. Chem. Chem. Phys. 28, 3779 (2025).
   <https://pubs.rsc.org/cp/article/28/6/3779/1247930/Contemporary-DFT-learning-from-traditional-and>
   (retrieved 2026-11-07).
6. Microsoft, `skala` reference implementation (MIT).
   <https://github.com/microsoft/skala> (retrieved 2026-11-07).
