---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [02-verification-log.md]
---

# Annotated bibliography

Every source used in this documentation set, with a note on what it is good
for, how much to trust it, and which part to actually read. The annotations are
opinionated on purpose: a bibliography that does not tell you what to skip is
just a list.

**Bottom line**

- The five sources that matter most are the challenge page, the NPA paper, the
  Skala paper, Transition1x, and the OMol25 paper. Read those first.
- The most *useful* source for this project is Skala's methods section, because
  it shows the winning mechanism (non-local mixing) explicitly.
- The most *dangerous* sources are benchmark tables without protocol notes.
  Treat every such table as a claim to be checked, not a fact.
- Three sources are secondary (a blog post, a benchmark aggregator, a
  news article). They are used only where a primary source was unavailable,
  and are flagged.

## Tier 1 — read these

### 1. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum Chemistry*

Problem 03, updated Nov 2026.
<https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
(retrieved 2026-11-07).

The statement of the problem the project is aimed at. Contains the task
definition, the submission requirements, the provisional leaderboard, and the
protocol. Short. Read all of it.

*Trust:* Primary, but written for a general audience and therefore leaves the
evaluation protocol partly implicit. The leaderboard payload is the most
valuable part and is machine-readable.

*Watch for:* the missing dispersion column, and the "other functionals being
evaluated" footnote, which means the board is already stale.

*Archived:* [`evidence/challenge-page.html`](evidence/challenge-page.html) and
[`evidence/challenge-leaderboard.js`](evidence/challenge-leaderboard.js),
checksums in [`evidence/retrieval.json`](evidence/retrieval.json).

### 2. Kim, Pajouheshgar, Süsstrunk, Jakob, Park, *Neural Particle Automata*

SIGGRAPH 2026, arXiv:2601.16096v3.
<https://arxiv.org/abs/2601.16096> (retrieved 2026-11-07).

The paper the whole project is built on. Read §3 (method), §4.4 (properties and
the multi-species demo), and the Limitations paragraph. The limitations
paragraph is more important than the results.

*Trust:* High. The paper is candid about what it does not do, which is unusual
and useful.

*Watch for:* the difference between what the videos show (composed independent
models) and what a reader assumes (a species mechanism). Also the detached
gradient trick, which is a stability hack with physical consequences.

*Do not read first:* the appendix derivations, unless you are reimplementing
the backward pass.

### 3. Luise et al., *Accurate and scalable exchange–correlation with deep learning* (Skala)

arXiv:2506.14665v6. <https://arxiv.org/abs/2506.14665> (retrieved 2026-11-07).

The current state of the art for the challenge's actual question. Read §2.2
(architecture), §2.3 (data), §3.1 (the non-local ablation), and Table 1.

*Trust:* High for the reported numbers; the code is MIT-licensed and available.

*Watch for:* the training data is not public (MSR-ACC). The comparison table
applies dispersion to all functionals, which is not what the challenge board
does. The paper is explicit that dispersion is not learned.

*Why it matters for this project:* the non-local mixing module is structurally
the same idea as particle perception. Skala is, in effect, evidence that the
NPA intuition works — implemented in the form DFT can consume.

### 4. Schreiner et al., *Transition1x*

Scientific Data 9, 2022; arXiv:2207.12858.
<https://www.nature.com/articles/s41597-022-01870-w> (retrieved 2026-11-07).

The canonical reactive dataset. 9.6M DFT calculations, 10k reactions,
ωB97x/6-31G(d), NEB-generated.

*Trust:* High. Widely used, well documented.

*Watch for:* it is path data, not dynamics. No velocities, no time. The level
of theory is modest.

*Key sentence:* "ML models cannot learn features in transition-state regions
solely by training on hitherto popular benchmark datasets." This is the
empirical justification for the entire project.

### 5. Levine et al., *The Open Molecules 2025 (OMol25) Dataset, Evaluations, and Models*

arXiv:2505.08762. <https://arxiv.org/abs/2505.08762> (retrieved 2026-11-07).

The largest molecular dataset, and the source of UMA. Read the abstract
carefully; it contains all the numbers you need. The body is 60 pages and is
mostly evaluation.

*Trust:* High for the dataset description. Lower for the model comparisons,
which are the authors' own.

*Watch for:* the level of theory is ωB97M-V, not CCSD(T). This caps everything
trained on it.

## Tier 2 — important supporting sources

### 6. Goerigk et al., *GMTKN55*

Phys. Chem. Chem. Phys. 19, 32184 (2017).
<https://doi.org/10.1039/C7CP04913G>.

The benchmark definition. You do not need to read all 32 pages; read the
introduction, the category structure, and the WTMAD-2 definition.

*Companion:* the Bonn group's web pages, which publish the WTMAD-2 tables with
and without dispersion —
<http://www.thc.uni-bonn.de/tc.old/downloads/GMTKN/GMTKN55/WTMAD-2-D3.html>.
These tables are how the dispersion asymmetry in the challenge leaderboard was
identified.

### 7. Bryenton and Johnson, *WTMAD-4: A Fair Weighting Scheme for GMTKN55*

arXiv:2509.23498. <https://arxiv.org/abs/2509.23498> (retrieved 2026-11-07).

The critique of WTMAD-2 and the source of the exact formula used here. Short,
technical, and worth reading if you will report any GMTKN55 number.

*Trust:* High. The flaw it identifies is real and acknowledged.

### 8. Kirkpatrick et al., *Pushing the frontiers of density functionals by solving the fractional electron problem* (DM21)

Science 374, 1385 (2021).
<https://www.science.org/doi/10.1126/science.abj6511>.

The proof of concept for learned functionals. Read the abstract and the
discussion; the methods are heavy.

*Trust:* High for the science, but the *adoption* story is the interesting part
and it is told elsewhere.

### 9. Bystrom and Kozinsky, *Nonlocal machine-learned exchange functional for molecules and solids*

Phys. Rev. B 110, 075130 (2024).
<https://link.aps.org/doi/10.1103/PhysRevB.110.075130>.

Useful mainly for its characterisation of DM21's cost: "computationally
expensive (even more so than global hybrid DFT) and not widely [used]". A
sober counterweight to benchmark enthusiasm.

### 10. Zhao et al., *Deep Mind 21 functional does not extrapolate to transition metal chemistry*

ChemRxiv (2024).
<https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2024-6bxhz>.

The title is the finding. Relevant because ALD/CVD precursor chemistry involves
metals.

### 11. Behler and Parrinello, *Generalized neural-network representation of high-dimensional potential-energy surfaces*

Phys. Rev. Lett. 98, 146401 (2007).
<https://doi.org/10.1103/PhysRevLett.98.146401>.

The origin of the modern MLIP. Read for the symmetry-function idea and the
locality assumption, both of which this project inherits.

### 12. Batzner et al., *NequIP*

Nature Communications 13, 2453 (2022).
<https://doi.org/10.1038/s41467-022-29939-5>.

The paper that established E(3)-equivariant tensor features as the standard.
Read the architecture section and the data-efficiency results.

### 13. Batatia et al., *MACE*

NeurIPS 2022; arXiv:2206.07697. <https://arxiv.org/abs/2206.07697>.

Higher body order without deep message passing. The best-supported general
architecture at the time of writing.

### 14. Musaelian et al., *Allegro*

Nature Communications 14, 579 (2023).
<https://doi.org/10.1038/s41467-023-36329-y>.

Strict locality done properly. The most relevant architecture if the project
wants a very fast, parallelisable model.

### 15. Leimeroth et al., *MLIPs from a user's perspective*

Modelling Simul. Mater. Sci. Eng. (2025).
<https://iopscience.iop.org/article/10.1088/1361-651X/adf56d/pdf>.

A practical comparison of accuracy, speed and data efficiency. Useful because
it is written by users, not authors, and reports where models fail.

### 16. Mordvintsev, Randazzo, Niklasson, Levin, *Growing Neural Cellular Automata*

Distill, 2020. <https://distill.pub/2020/growing-ca/>.

The origin of the NCA line. Read for the training recipe (pool, stochastic
mask, overflow loss) and for the regeneration result. Note that the objective
is an image, not a trajectory.

### 17. Meta FAIR, OMol25 and UMA announcement

<https://ai.meta.com/blog/meta-fair-science-new-open-source-releases/>
(retrieved 2026-11-07).

*Secondary source.* Used only for context on release and licensing. All
technical numbers come from the arXiv paper.

## Tier 3 — used with caution

### 18. Rowan Benchmarks, GMTKN55 for MLIPs

<https://benchmarks.rowansci.com/benchmarks/gmtkn55> (retrieved 2026-11-07).

*Secondary source* — an aggregator, not a paper. Valuable because almost no
MLIP paper reports GMTKN55, and Rowan does it consistently across models. But:

- It exposes six WTMAD variants; the default is not always obvious.
- The evaluation protocol (basis, dispersion, geometry source) is not fully
  documented on the page.
- The page was read via a search extract, not archived in full.

Use it for the *pattern* (materials models fail on molecules; UMA is close to
hybrids; barriers lag), not for precise numbers.

### 19. Brémond et al., *Contemporary DFT*

Phys. Chem. Chem. Phys. 28, 3779 (2025).
<https://pubs.rsc.org/cp/article/28/6/3779/1247930/Contemporary-DFT-learning-from-traditional-and>.

A recent survey. Useful for the statement that DM21's developers caution
against elements heavier than Kr. Read the DM21 and Skala sections only.

### 20. Pajouheshgar et al., NPA project page

<https://selforg-npa.github.io/> (retrieved 2026-11-07).

Interactive demos and the SPH perception explainer. The explainer is genuinely
the best explanation of the SPH operators available, better than the paper's
equations for building intuition. Note that "multi-species" on this page means
composed independent models.

## What is missing from this bibliography

Deliberately, because it was not verified:

- Named reactive-potential methods (neural EVB, diffusion-based TS generation,
  learned collective variables). Discussed by category in
  [reactive potentials](../02-prior-art/07-reactive-potentials-and-enhanced-sampling-models.md),
  not cited individually.
- Transition-metal-specific datasets and benchmarks.
- Surface science and periodic-boundary method references.
- The original transition-state theory papers (Eyring, Evans–Polanyi), which are
  textbook material and do not need a citation here.

Adding any of these requires a verification-log entry first.

> **In plain words.** Everything in this list was opened and checked. The
> things that were not checked are listed as missing rather than
> half-remembered.

## How to use this list

- **If you have one day:** items 1–5.
- **If you have one week:** add 6–9, 12–16.
- **If you are reviewing a claim:** go to
  [the verification log](02-verification-log.md) first, then the source.
- **If you are writing:** cite the primary source, never this bibliography.

## Open questions

- Should the evidence archive include the Skala and NPA PDFs, not just the
  challenge page? Yes, if the project will cite them repeatedly.
- Is there a canonical citation for the ALD/CVD precursor chemistry? Not yet
  identified; needed before the chemistry document can be considered complete.

## What would change this document

- New releases (Skala-1.2, a new OMol25 version, a reactive benchmark).
- Verification of the currently-uncited reactive methods.
- A published challenge evaluation protocol.

## Sources

This document annotates the sources listed above; each entry carries its own
URL and retrieval date. No independent claims are made here that are not
sourced elsewhere in the set.
