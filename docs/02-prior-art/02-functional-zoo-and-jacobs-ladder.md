---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [../01-science/02-density-functional-theory.md]
---

# The functional zoo and Jacob's ladder

Jacob's ladder is the organising metaphor of density functional theory: each
rung adds one ingredient to the exchange–correlation functional, buys some
accuracy, and costs some compute. It is genuinely useful for orientation. It is
also misleading in two ways that matter for this project — it implies a single
ladder when the field is a thicket of sideways variants, and it implies that
climbing is always worth it when the cost curve is brutally non-linear.

**Bottom line**

- There are five rungs worth knowing: LDA, GGA, meta-GGA, hybrid, and
  double-hybrid/RPA. Cost climbs from $O(N^3)$ to $O(N^5)$ or worse.
- The single biggest accuracy jump for reaction chemistry is **adding exact
  exchange** (hybrid), followed by **getting dispersion right** (a correction,
  not a rung).
- The field contains hundreds of functionals, many fitted to the same
  benchmarks. Choosing the best one on GMTKN55 is a selection problem, not a
  discovery.
- On the challenge's own leaderboard, ωB97M-V is best at 3.81 kcal/mol and
  costs 43.5 s/molecule versus 2.4 s for LDA — an 18× cost increase for a 7×
  error reduction.
- For this project, the relevant baselines are PBE (the cheap workhorse),
  ωB97M-V (the accurate ceiling), and one learned functional (Skala) as the
  modern comparator. Nothing else earns its place in the table.

## The ladder, rung by rung

| Rung | Extra ingredient | Representative functionals | Asymptotic cost | What it fixes | What it does not |
|---|---|---|---|---|---|
| **LDA** | $\rho$ only | LDA (VWN, PW92 correlation) | $O(N^3)$ | Nothing much; a baseline | Everything |
| **GGA** | $\nabla\rho$ | PBE, B88+LYP (BLYP), PW91, revPBE | $O(N^3)$ | Inhomogeneity; bond energies much better than LDA | Dispersion, static correlation, self-interaction |
| **meta-GGA** | $\tau$ (kinetic energy density), sometimes $\nabla^2\rho$ | TPSS, SCAN, r²SCAN, B97M-V, M06-L | $O(N^3)$ | Better atomisation and barriers; SCAN is the modern default | Dispersion (unless built in), exact exchange |
| **Hybrid** | exact (Hartree–Fock) exchange, usually 20–25% | B3LYP, PBE0, HSE06, M06-2X | $O(N^4)$ | Delocalisation error, barrier heights | Dispersion, strong correlation |
| **Range-separated hybrid** | exact exchange with distance-dependent fraction | CAM-B3LYP, ωB97X-V, ωB97M-V | $O(N^4)$ | Charge-transfer and long-range self-interaction | Dispersion (unless VV10 built in) |
| **Double hybrid / RPA** | virtual orbitals (MP2-like correlation) | B2PLYP, DSD-PBEP86, RPA | $O(N^5)$+ | Non-local correlation, good thermochemistry | Cost; still not exact |

Two facts about this table are routinely under-weighted.

**Exact-exchange fraction is a design variable, not a physical constant.**
B3LYP uses 20%, PBE0 25%, M06-2X 54%, HSE06 25% but screened to short range.
The "right" fraction depends on the property and the training set. This is
already a form of fitting, which is why the line between "hand-designed" and
"learned" functional is blurrier than it appears.

**Dispersion is not a rung.** It is a separate physical effect — instantaneous
dipole–dipole correlation — that most semi-local functionals miss entirely. It
is added as a correction: D3(0) (original), D3(BJ) (Becke–Johnson damping, the
modern default), D4 (charge-dependent), VV10 (non-local correlation, built into
some functionals), or MBD (many-body dispersion). On a benchmark containing
non-covalent interactions, omitting it can double the error. See
[GMTKN55 mechanics](04-gmtkn55-and-benchmark-mechanics.md) for why this
dominates the challenge leaderboard.

> **In plain words.** Each rung of the ladder gives the functional more
> information about the electrons: first just how crowded they are, then how
> the crowd changes from place to place, then how fast they are moving, then
> some exact quantum exchange. Each step costs more. Dispersion is not a rung
> at all — it is a separate patch for the weak stickiness between molecules
> that the ladder never captures.

## The six leaderboard functionals, placed

| Functional | Rung | Exact exchange | Dispersion on leaderboard? | WTMAD-2 (kcal/mol) | CPU s/molecule |
|---|---|---|---|---|---|
| LDA | LDA | 0% | no | 26.35 | 2.4 |
| PBE | GGA | 0% | no | 12.47 | 3.0 |
| B3LYP | hybrid | 20% | no | 16.16 | 4.0 |
| PBE0 | hybrid | 25% | no | 8.37 | 3.9 |
| HSE06 | screened hybrid | 25% (short-range) | no | 8.29 | 12.2 |
| ωB97M-V | range-separated hybrid + VV10 | ~15–100% by range | **built in (VV10)** | 3.81 | 43.5 |

All values from the challenge's provisional leaderboard, def2-QZVP, single CPU
core, median of three runs
([challenge page](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/),
retrieved 2026-11-07).

Three readings of this table:

1. **B3LYP is worse than PBE here**, which is not the usual story. The reason
   is dispersion: B3LYP without D3 is catastrophic on the non-covalent subsets,
   and PBE's error happens to be more evenly distributed. This is a warning
   about reading a single number.
2. **HSE06 costs 3× PBE0 for essentially the same error.** Screening helps
   solids, not this benchmark.
3. **ωB97M-V is the only entry below 4 kcal/mol**, and it pays for it: 43.5 s,
   about 11× PBE. It also has VV10 built in, so part of its advantage is
   dispersion that the others were not given.

> **In plain words.** Look at B3LYP sitting above PBE even though B3LYP is
> normally the better method. That is what happens when you test a method
> without the patch it needs. The table is measuring the methods as shipped,
> not as used.

## The zoo problem

Skala's introduction states the situation plainly: users "must still choose
from among hundreds of XC functional approximations." The consequences:

- **Selection bias.** If you try 50 functionals on one benchmark and report the
  best, your reported error is an order statistic, not an expected error.
- **Benchmark entanglement.** Many functionals were fitted to subsets of
  GMTKN55 or its ancestors. Evaluating them on it is partly a memory test.
- **Diminishing returns.** The difference between the 5th-best and 15th-best
  functional on GMTKN55 is often within the spread across implementations,
  basis sets, and grid choices.
- **No retirement.** Unlike software, functionals accumulate. The 1990s ones
  are still in every code because someone's published result depends on them.

This is why Skala's authors explicitly position their model as versioned —
"successive releases superseding their predecessors" — rather than as one more
entry in the zoo. That is a cultural intervention as much as a technical one.

*(inference)* For this project, the practical rule is: pick two functionals,
justify them, and never report a best-of-many without saying how many you
tried.

> **In plain words.** There are hundreds of these recipes, many were tuned on
> the same exam, and nobody throws the old ones away. So "the best functional"
> is partly a story about who tried the most recipes on that particular exam.

## Why "just use ωB97M-V" is not the answer

It is tempting: 3.81 kcal/mol, best on the board, well-tested. Three reasons it
does not close the problem:

1. **Cost.** 43.5 s per molecule on one core, versus 2.4 s for LDA. At scale
   that is the difference between screening thousands of candidates and
   screening millions. The challenge explicitly scores compute time.
2. **It is still 3.8× above the target.** Chemical accuracy is 1 kcal/mol. The
   gap is not a rounding error; it is the difference between a useful
   prediction and a guess for barrier heights.
3. **It is a range-separated hybrid with VV10**, so it is already near the top
   of the hand-designed ladder. There is no obvious next rung to climb — which
   is precisely why learned non-locality is the interesting direction.

The honest framing: ωB97M-V is the *ceiling of the hand-designed approach*, and
the ceiling is below the requirement. That is the argument for learning, not
for switching functionals.

> **In plain words.** The best hand-built recipe is still four times too wrong
> and eighteen times slower than the cheapest one. You cannot fix that by
> picking a different recipe from the same cookbook.

## Where each rung fails for reaction chemistry

| Failure | Rungs affected | Symptom | Why |
|---|---|---|---|
| **Self-interaction error** | LDA, GGA, meta-GGA | Over-delocalised electrons, underestimated barriers | An electron repels itself in the Hartree term; semi-local functionals cannot cancel it |
| **Delocalisation error** | all semi-local | Stretched bonds too stable, charge transfer too easy | Related to self-interaction; worst at dissociation |
| **Missing dispersion** | all without a correction | Binding energies far too weak | Instantaneous correlation is non-local |
| **Static correlation** | all single-reference | Wrong for bond breaking, diradicals, some metals | Requires multiple determinants; DFT with one determinant cannot represent it |
| **Basis-set incompleteness** | all | Errors that mimic functional errors | Small bases are variationally biased |
| **Spin contamination** | hybrids especially | Wrong energetics for open-shell systems | Hartree–Fock exchange mixes spin states |

The first three are the ones that matter most for barrier heights, which is
what the challenge scores.

> **In plain words.** Three things go wrong over and over: electrons attract
> themselves too much, molecules that should drift apart stick together, and
> bonds that are breaking are described by a theory that assumes they are not.
> Those three account for most of the error in reaction barriers.

## Recommendation for this project

Use this baseline set and no more:

| Role | Choice | Why |
|---|---|---|
| Cheap reference | PBE | Fast, ubiquitous, the honest lower bound |
| Accurate reference | ωB97M-V | Best on the challenge board; the target to beat |
| Modern comparator | Skala-1.1 | The learned-functional state of the art |
| Sanity check | B3LYP-D3(BJ) | Catches "we forgot dispersion" errors |

If a learned model cannot beat PBE on cost and ωB97M-V on accuracy
simultaneously, it has no claim. If it can beat B3LYP-D3(BJ) on both, that is a
publishable first result.

> **In plain words.** Four reference points are enough: the cheap one, the
> accurate one, the new learned one, and one that catches the most common
> mistake. More than that is decoration.

## Open questions

- Is there a hand-designed functional published after ωB97M-V that is
  competitive at lower cost? The field moves; this needs an annual check.
- How much of the leaderboard's B3LYP penalty is dispersion versus basis-set
  sensitivity? A controlled rerun would settle it.
- Does the challenge's hidden benchmark weight barriers heavily enough that a
  barrier-specialised functional would win despite poor thermochemistry?

## What would change this document

- A new rung appearing (e.g. a widely adopted local hybrid with
  machine-learned components at GGA cost).
- The challenge organisers publishing the exact functional settings they used.
- A demonstration that a meta-GGA plus a good dispersion correction reaches
  chemical accuracy on the hidden benchmark, which would undercut the case for
  learned functionals entirely.

## Sources

1. Goerigk et al., *A look at the density functional theory zoo with the
   advanced GMTKN55 database*, Phys. Chem. Chem. Phys. 19, 32184 (2017).
   <https://doi.org/10.1039/C7CP04913G> (retrieved 2026-11-07).
2. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry*. <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07).
3. Luise et al., *Accurate and scalable exchange–correlation with deep
   learning* (Skala), arXiv:2506.14665v6, §1 and Table 1.
   <https://arxiv.org/abs/2506.14665> (retrieved 2026-11-07).
4. Grimme group, WTMAD-2 tables with and without dispersion.
   <http://www.thc.uni-bonn.de/tc.old/downloads/GMTKN/GMTKN55/WTMAD-2-D3.html>
   (retrieved 2026-11-07).
