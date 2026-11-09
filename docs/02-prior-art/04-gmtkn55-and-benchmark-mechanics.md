---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [02-functional-zoo-and-jacobs-ladder.md, 03-learned-exchange-correlation-functionals.md]
---

# GMTKN55 and benchmark mechanics

The challenge scores submissions on a hidden benchmark but asks entrants to
demonstrate accuracy on GMTKN55, a public one. Understanding what GMTKN55
actually measures — and what it does not — is the difference between reading
the leaderboard correctly and drawing the wrong conclusion from it. This
document is the mechanics; the interpretation lives in
[the provisional leaderboard](../06-leaderboard/01-provisional-leaderboard.md).

**Bottom line**

- GMTKN55 is 55 subsets of *relative* energies — reaction energies, barrier
  heights, and non-covalent interaction energies — referenced to CCSD(T)-based
  values. It is a thermochemistry and kinetics benchmark, not a dynamics one.
- WTMAD-2 is a weighted average of per-subset mean absolute deviations. Each
  subset is weighted by its share of reactions and by the ratio of the mean
  absolute reference energy to that subset's mean. This deliberately
  down-weights atomisation energies, where raw errors are naturally large.
- The weighting is known to be unfair in the tails: some subsets contribute
  orders of magnitude less than others. WTMAD-3 and WTMAD-4 exist to fix this.
  Reassuringly, the ranking of good functionals is broadly stable across
  variants; the ranking of bad ones is not.
- **The challenge's provisional leaderboard appears to be evaluated without
  dispersion corrections.** This is the single most important interpretive
  fact, and it is not stated on the page.
- GMTKN55 contains almost no transition-metal organometallic chemistry and no
  ALD/CVD precursor chemistry. A good GMTKN55 score is necessary, not
  sufficient, for the hidden benchmark.

## What GMTKN55 contains

Goerigk, Hansen, Bauer, Ehrlich, Najibi and Grimme, *A look at the density
functional theory zoo with the advanced GMTKN55 database for general main group
thermochemistry, kinetics and noncovalent interactions*, Phys. Chem. Chem.
Phys. 19, 32184 (2017),
[DOI 10.1039/C7CP04913G](https://doi.org/10.1039/C7CP04913G).

It is an extension of GMTKN30 and contains 55 subsets, grouped into five
categories:

| Category | What it tests | Examples |
|---|---|---|
| **Basic properties and reaction energies, small systems** | Atomisation, ionisation, electron affinity, proton affinity, bond dissociation | W4-11, G21EA, G21IP, PA26, SIE4x4, ALKBDE10 |
| **Isomerisation and reaction energies, large systems** | Isomerisation, fragmentation, Diels–Alder, radical stabilisation | ISO34, ISOL24, DARC, RSE43, C60ISO |
| **Barrier heights** | Reaction barriers across mechanisms | BH76, BHDIV10, BHPERI, INV24, PX13, WCPT18 |
| **Intermolecular non-covalent interactions** | Dimers, hydrogen bonds, halogen bonds, rare-gas complexes | S22, S66, HAL59, AHB21, WATER27 |
| **Intramolecular non-covalent interactions** | Conformers, intramolecular dispersion | ACONF, PCONF21, IDISP, SCONF |

Reference values are CCSD(T)-based, with basis-set extrapolation and, for the
most demanding subsets, composite thermochemical protocols. They are *not*
exact: see [wavefunction methods and error bars](../01-science/03-wavefunction-methods-and-error-bars.md).

Note what is absent: solids, surfaces, explicit dynamics, temperature-dependent
free energies, and — critically for this project — organised transition-metal
precursor chemistry. There is an `AL2X6` subset (AlX₃ dimerisation) and
`ALK8`/`ALKBDE10` for alkali/alkaline chemistry, which is the closest thing to
ALD precursors in the whole benchmark.

> **In plain words.** GMTKN55 is fifty-five quizzes about how much energy is
> released or absorbed when molecules rearrange, plus how strongly they stick
> together. It is a broad exam, but it is an exam about *energy differences at
> fixed geometries*, not about how fast anything happens or how molecules move.

## The WTMAD-2 formula

A plain mean of per-subset errors would be dominated by subsets with large
absolute energy scales — atomisation energies are hundreds of kcal/mol, so a 1%
error there is several kcal/mol, while a 1% error on a conformer energy
difference is a fraction of a kcal/mol. WTMAD-2 corrects for this.

$$
\mathrm{WTMAD\text{-}2}
= \sum_{i=1}^{N_{\text{bench}}}
\frac{N_i}{N_{\text{total}}}
\cdot
\frac{\overline{|\Delta E|}_{\text{mean}}}{\overline{|\Delta E|}_i}
\cdot
\mathrm{MAD}_i,
$$

where:

- $N_i$ is the number of reactions in subset $i$, $N_{\text{total}}$ the total;
- $\mathrm{MAD}_i$ is the mean absolute deviation on subset $i$;
- $\overline{|\Delta E|}_i$ is the mean absolute reference energy of subset $i$;
- $\overline{|\Delta E|}_{\text{mean}}$ is the mean of those means over all
  subsets.

The middle factor is a normalisation: subsets whose reference energies are
large get their errors scaled down; subsets with small reference energies get
scaled up. The first factor weights by how much data the subset contains.

This is why a functional can look good on WTMAD-2 while being terrible on, say,
barrier heights: barrier subsets are a small share of the reaction count and
have moderate energy scales. **WTMAD-2 is a summary statistic, and summaries
hide structure.** Always look at the category breakdown.

> **In plain words.** Some quizzes have huge numbers (burning a molecule
> completely) and some have tiny ones (which shape a molecule prefers). If you
> just averaged the mistakes, the huge-number quizzes would drown everything
> out. WTMAD-2 rescales each quiz so the small-number ones still count.

## Known flaws in the weighting

Bryenton and Johnson, *WTMAD-4: A Fair Weighting Scheme for GMTKN55*,
[arXiv:2509.23498](https://arxiv.org/abs/2509.23498), identify a real problem:
the WTMAD-2 weights "under-weight some of its component benchmarks by orders of
magnitude."

Their fixes:

- **WTMAD-3** (Wittmann et al.) caps any subset's contribution at 1% of total
  reactions: $N_i^{\text{damp}} = \max(0.01 N_{\text{total}}, N_i)$.
- **WTMAD-4** sets weights from the typical errors of ten minimally empirical
  dispersion-corrected functionals, rather than from energy scales.

The practical consequence for reading leaderboards: **do not compare a WTMAD-2
from one source with a WTMAD-2 from another source** unless you know they used
the same variant. The Rowan benchmark site, for example, exposes six different
WTMAD schemes and labels them explicitly
([benchmarks.rowansci.com](https://benchmarks.rowansci.com/benchmarks/gmtkn55),
retrieved 2026-11-07).

*(inference)* For this project the safe practice is to report WTMAD-2 as the
headline — because that is what the challenge uses — and to report per-category
MADs alongside it, so that a reader can see whether a gain came from
thermochemistry, barriers, or non-covalent interactions.

> **In plain words.** The weighting scheme was invented to be fair, and it is
> not entirely fair. Different versions of it give different rankings for
> mediocre methods. So a single number is not enough; you need to know which
> version and how the categories moved.

## The dispersion problem, and why the leaderboard is misleading

This is the most important thing in this document.

The challenge's provisional leaderboard reports B3LYP at **16.16 kcal/mol** and
PBE at **12.47** ([challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/),
retrieved 2026-11-07). The Grimme group's published WTMAD-2 tables report
B3LYP-D3(BJ) at **6.42** and PBE-D3(BJ) at **10.32**
([Bonn GMTKN55 WTMAD-2 page](http://www.thc.uni-bonn.de/tc.old/downloads/GMTKN/GMTKN55/WTMAD-2-D3.html),
retrieved 2026-11-07).

The gap is too large to be a basis-set or grid artefact. It is dispersion:
B3LYP without a dispersion correction is roughly 16 kcal/mol on GMTKN55;
with D3 it is roughly 6.4. The challenge numbers sit squarely in the
*uncorrected* column.

Why does this matter?

1. **The leaderboard compares default implementations, not best practice.**
   Nobody who knows what they are doing runs B3LYP without dispersion on a
   benchmark containing non-covalent interactions. The table therefore
   overstates the difficulty of reaching low errors with conventional
   functionals.
2. **ωB97M-V looks unusually good partly because it has non-local correlation
   built in.** VV10 is part of the functional, not a bolt-on, which is why its
   cost is 43.5 s versus 4.0 s for B3LYP. It is not an apples-to-apples
   comparison with an uncorrected hybrid.
3. **A learned functional trained with dispersion will look better than the
   leaderboard suggests.** Skala is trained with a *fixed D3 correction* and
   reports 2.80 with D3(BJ) applied to all baselines. On a dispersion-free
   leaderboard, that comparison would be different.
4. **The target of <1 kcal/mol is harder than it looks in the uncorrected
   table, and easier than it looks in the corrected one.** Both statements are
   true, and neither is stated on the page.

*(inference)* The most likely explanation is that the leaderboard uses
default functional implementations from a quantum chemistry code with no
empirical dispersion, which is a defensible choice for measuring "the
functional as published" but a poor choice for measuring "what this method can
do".

**Recommendation for this project.** Report both: the functional as published,
and the functional with a stated dispersion correction. Never mix the two in
one table.

> **In plain words.** The scoreboard is comparing bare, uncorrected versions of
> the old methods, while the newest method has its long-range physics built in.
> That makes the old methods look worse than they are and the target look
> further away. If we ever publish a table, we must say which version we ran.

## What GMTKN55 does not measure

Six gaps that matter for a reaction surrogate:

| Gap | Consequence |
|---|---|
| **No dynamics** | A functional can nail barrier heights and still give wrong rates; GMTKN55 cannot see this |
| **Almost no transition metals** | ALD/CVD precursors often contain Al, Ti, Cu, Hf; GMTKN55 is main-group |
| **No surfaces** | ALD is a surface reaction; gas-phase clusters are a proxy at best |
| **No temperature or entropy** | All quantities are electronic energy differences at 0 K |
| **No explicit solvent** | Solution-phase chemistry is out of scope |
| **No reaction rates or selectivities** | The industrially relevant outputs are absent |

The hidden benchmark is described as "reference-quality molecular reaction
energies, activation barriers, binding energies, and bond dissociation energies
representative of atomic layer deposition (ALD) and chemical vapour deposition
(CVD) precursor chemistry"
([challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/)).
That is still static energetics, but in a chemical space GMTKN55 barely covers.

> **In plain words.** The public exam tests a broad slice of ordinary organic
> chemistry. The private exam tests the specific chemistry of making thin films
> from metal-containing gases. Doing well on the first is a good sign, not a
> guarantee, for the second.

## How to read a leaderboard honestly

A checklist to apply to any table of functional or potential performance,
including this project's own.

1. **What is the reference?** CCSD(T)/CBS, experimental, or another functional?
   A model trained on ωB97M-V and evaluated against ωB97M-V will look perfect.
2. **Is dispersion included, and how?** D3(0), D3(BJ), D4, VV10, or none.
3. **What basis set?** def2-QZVP is near-complete for main-group; def2-SVP is
   not, and basis-set error can exceed functional error.
4. **What hardware, and what timing protocol?** Single core, median of three,
   as the challenge states. GPU timings are not comparable.
5. **Mean or median?** A single catastrophic failure can dominate a mean.
6. **Error bars?** The challenge gives 95% intervals, e.g. PBE 12.47
   (10.34–14.50). Overlapping intervals mean "indistinguishable", not "better".
7. **Training-set overlap.** Was the benchmark in the training data? At what
   level — molecule, graph, conformer?
8. **What is missing from the table?** Usually: the cost of the best method,
   the accuracy of the cheapest, and any method that failed to converge.

> **In plain words.** Eight questions turn a table from a scoreboard into
> evidence. Most of them are about what the table left out.

## Applying this to the challenge

The challenge's evaluation has three axes: accuracy, compute time per molecule,
and reproducibility. GMTKN55 addresses only the first, on public chemistry.
A serious submission therefore needs:

- GMTKN55 results **with protocol stated** (basis, dispersion, grid, code
  version), and ideally per-category breakdown.
- Timing on the same footing as the leaderboard: single CPU core, def2-QZVP,
  median of three.
- A statement of what the method does on chemistry *not* in GMTKN55 —
  transition-metal precursors, surface models, open-shell intermediates.
- Evidence of reproducibility: pinned code, container, and a script that
  regenerates the table.

For an NPA-based project, the first and third items are the hard ones. A
dynamics surrogate has no natural GMTKN55 number at all unless it is built
around an energy. This is the core of
[challenge fit](../06-leaderboard/02-challenge-fit-analysis.md).

> **In plain words.** To be taken seriously by the competition you need three
> things: the public exam score, the speed, and proof that someone else can
> reproduce both. A model that only produces trajectories cannot even sit the
> exam.

## Open questions

- Which WTMAD variant does the challenge actually use internally? The page says
  "WTMAD-2" and links the 2017 paper, so presumably the original. Worth
  confirming if a submission is ever made.
- Is the challenge leaderboard's lack of dispersion deliberate or incidental?
  The page does not say. This should be asked, not assumed.
- How will the hidden ALD/CVD benchmark weight barriers against binding
  energies? The relative weighting determines which functional errors matter.

## What would change this document

- A published methods note from the challenge organisers specifying the
  evaluation protocol in detail.
- Evidence that the leaderboard numbers do include dispersion and the gap has
  another cause, which would require revising the central claim here.
- A WTMAD-5 or a decision by the community to standardise on WTMAD-4, which
  would make WTMAD-2 comparisons obsolete.

## Sources

1. Goerigk et al., *A look at the density functional theory zoo with the
   advanced GMTKN55 database*, Phys. Chem. Chem. Phys. 19, 32184 (2017).
   <https://doi.org/10.1039/C7CP04913G> (retrieved 2026-11-07).
2. Grimme group, GMTKN55 database overview and subset list.
   <https://www.chemie.uni-bonn.de/grimme/de/software/gmtkn/gmtkn55> (retrieved
   2026-11-07).
3. Grimme group, WTMAD-2 tables with and without dispersion.
   <http://www.thc.uni-bonn.de/tc.old/downloads/GMTKN/GMTKN55/WTMAD-2-zero.html>
   and
   <http://www.thc.uni-bonn.de/tc.old/downloads/GMTKN/GMTKN55/WTMAD-2-D3.html>
   (retrieved 2026-11-07).
4. Bryenton and Johnson, *WTMAD-4: A Fair Weighting Scheme for GMTKN55*,
   arXiv:2509.23498. <https://arxiv.org/abs/2509.23498> (retrieved 2026-11-07).
5. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry*. <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07).
6. Rowan Benchmarks, GMTKN55 results across WTMAD schemes.
   <https://benchmarks.rowansci.com/benchmarks/gmtkn55> (retrieved 2026-11-07).
