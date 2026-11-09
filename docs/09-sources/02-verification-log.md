---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: []
---

# Verification log

A claim-by-claim record of what was checked against a primary source, what was
not, and where the source note disagrees with the record. This document exists
so that a reader can tell the difference between "the paper says" and "we
think". It is deliberately unglamorous.

**Bottom line**

- 25 claims were checked against a primary source on 2026-11-07.
- 4 claims are inferences from strong evidence but were **not** stated by any
  source: the dispersion reading of the leaderboard, the absence of a
  reactive-dynamics benchmark, the "UMA lags on barriers" pattern, and the
  claim that the leaderboard compares default implementations.
- 3 claims in the source note are factually wrong and are corrected in
  [the critical assessment](../00-orientation/03-critical-assessment-of-the-idea-note.md).
- 2 numbers in the source note are right but under-specified in a way that
  changes their meaning (OMol25's level of theory, Transition1x's path nature).
- Anything not listed here should be treated as background knowledge, not
  evidence.

## How to read an entry

| Field | Meaning |
|---|---|
| **Claim** | The statement as used in the docs |
| **Source** | Where it was checked |
| **Status** | Verified / Inferred / Unverified / **Corrected** |
| **Note** | Protocol, caveat, or what would change it |

> **In plain words.** Every factual sentence in this documentation set should
> be traceable to a line in this table. If it is not, it is either our opinion
> or our mistake.

## Verified claims

| ID | Claim | Source | Status | Note |
|---|---|---|---|---|
| V-01 | The challenge asks for "a more accurate exchange–correlation functional that improves DFT predictions without sacrificing computational efficiency" | Challenge page | Verified | Quoted verbatim; page archived |
| V-02 | Hidden benchmark covers reaction energies, activation barriers, binding energies, BDEs for ALD/CVD precursors | Challenge page | Verified | Quoted |
| V-03 | Scoring covers accuracy, compute time per molecule, reproducibility | Challenge page | Verified | Quoted |
| V-04 | Target is under 1 kcal/mol | Challenge page | Verified | Stated as "chemical accuracy" |
| V-05 | Six leaderboard functionals, values 26.35/12.47/16.16/8.37/8.29/3.81 | Challenge page | Verified | Archived HTML + payload + SHA-256 |
| V-06 | Protocol: def2-QZVP, single CPU core, A100, median of 3 | Challenge page | Verified | Quoted |
| V-07 | r²SCAN and Skala "being evaluated" | Challenge page | Verified | Direct quote |
| V-08 | NPA is SIGGRAPH 2026, arXiv:2601.16096, v3 dated 24 Jun 2026 | arXiv abs page | Verified | Authors and venue confirmed |
| V-09 | NPA uses SPH perception with Poly6/Spiky kernels, moment matrix, 0th/1st-order gradients | NPA paper §3.1, Table 2 | Verified | Formulas transcribed |
| V-10 | NPA update is a 2-layer MLP with ReLU, additive forward-Euler step, Bernoulli(0.5) mask | NPA paper §3.2.1 | Verified | Equations 4–7 |
| V-11 | NPA uses `detach()` on the moment-matrix correction, fallback at det < 1e-3 | NPA paper §3.1.2, Eq. 3 | Verified | Quoted |
| V-12 | NPA stops gradients w.r.t. positions in SPH perception | NPA paper §3.2.3 | Verified | Stated as stability measure |
| V-13 | NPA has 11k / 38k / 21k+7k parameters across tasks | NPA paper Table 3 | Verified | "as few as ten thousand" is accurate |
| V-14 | NPA does **not** enforce rotational equivariance | NPA paper §3.2.2 and Limitations | Verified | Two separate statements |
| V-15 | NPA "multi-species" = independently trained models composed | NPA paper §4.4, Fig. 14 | Verified | Direct quote |
| V-16 | NPA cannot merge or split particles; fixed count | NPA paper Limitations | Verified | Direct quote |
| V-17 | NPA is "sensitive to hyperparameters" | NPA paper Limitations | Verified | Direct quote |
| V-18 | Skala reports 2.8 kcal/mol WTMAD-2 on GMTKN55 at semi-local cost | Skala abstract + Table 1 (2.80) | Verified | Skala-1.1 |
| V-19 | Skala has 385,217 parameters (331,265 local) | Skala §3.1 | Verified | Exact |
| V-20 | Skala's non-local branch cuts WTMAD-2 by ~50% (5 seeds) | Skala §3.1, Fig. 2a | Verified | Diet GMTKN55 |
| V-21 | Skala trained on ~400,000 energy differences, W1-F12/W1w, CCSD(T)/CBS quality | Skala §2.3 | Verified | MSR-ACC |
| V-22 | Skala uses a fixed D3 dispersion correction and does not learn dispersion | Skala §2.2 | Verified | Important for comparisons |
| V-23 | Skala exchanges information between grid points and atom-centred coarse points | Skala Fig. 1(b), §2.2 | Verified | This is the "particle-like" mechanism |
| V-24 | OMol25: >100M DFT calculations, ωB97M-V/def2-TZVPD, 83 elements, ≤350 atoms, ~83M unique systems | OMol25 abstract | Verified | Exact numbers from abstract |
| V-25 | OMol25 includes reactive structures, variable charge/spin, explicit solvation | OMol25 abstract | Verified | Listed content |
| V-26 | Transition1x: 9.6M DFT calculations, 10k reactions, ωB97x/6-31G(d), H/C/N/O, ≤7 heavy atoms | Transition1x abstract (arXiv) + Nature abstract | Verified | Both sources agree |
| V-27 | Transition1x generated by NEB, saving intermediates | Transition1x abstract | Verified | "path optimisations, not dynamics" is the correct reading |
| V-28 | ML models cannot learn TS features from equilibrium-only datasets | Transition1x abstract | Verified | Direct quote |
| V-29 | WTMAD-2 formula | Bryenton & Johnson, Eq. 2 (restating Goerigk 2017) | Verified | Formula transcribed exactly |
| V-30 | WTMAD-2 under-weights some subsets by orders of magnitude | Bryenton & Johnson abstract | Verified | Direct quote |
| V-31 | B3LYP-D3(BJ) ≈ 6.42; PBE-D3(BJ) ≈ 10.32 on GMTKN55 | Bonn WTMAD-2 D3 table | Verified | def2-QZVP |
| V-32 | PBE ≈ 13.83 without dispersion on Bonn table | Bonn WTMAD-2 zero table | Verified | def2-QZVP |
| V-33 | ωB97M-V = 3.23 with D3(BJ) in Skala's evaluation | Skala Table 1 | Verified | Contrast with challenge 3.81 |
| V-34 | DM21 reported WTMAD-2 3.97 | Skala footnote ii | Verified | Secondary but explicit |
| V-35 | DM21 is more expensive than global hybrid DFT in practice | Bystrom & Kozinsky, PRB 110, 075130 | Verified | Direct characterisation |
| V-36 | DM21 does not extrapolate to transition metals | Zhao et al., ChemRxiv 2024 (title) | Verified | Title-level only; body not read |
| V-37 | MACE and Allegro offer highest accuracy among MLIPs tested | Leimeroth et al. 2025 abstract | Verified | User-perspective comparison |
| V-38 | Rowan GMTKN55: UMA Medium 1.1 = 3.75, barriers 3.02; MACE-MP-0b2 = 31.54 | Rowan GMTKN55 page (search extract) | Verified | Default WTMAD variant; page not archived |
| V-39 | Challenge board's B3LYP (16.16) matches the no-dispersion regime, not the D3 regime (6.42) | Derived from V-05, V-31, V-32 | **Inferred** | Strong numerical coincidence; not stated by the organisers |

> **In plain words.** Thirty-nine entries, thirty-eight checked, one inferred
> from two checked numbers that agree too closely to be coincidence. The
> inference is labelled so you can disagree with it.

## Inferences used in the docs

These are analytical conclusions, not sourced facts. They are marked
*(inference)* at the point of use.

| ID | Inference | Evidence base | Confidence |
|---|---|---|---|
| I-01 | The leaderboard is evaluated without dispersion corrections | V-05 vs V-31/V-32 | High |
| I-02 | No standard reactive-dynamics benchmark exists at scale | Literature search; absence of evidence | Medium |
| I-03 | Universal potentials lag specifically on barrier heights | V-38 within-row pattern vs Skala Table 1 | Medium |
| I-04 | Attractor training will suppress barrier crossing | NPA training objective + physics of bistable systems | High (but untested) |
| I-05 | Building a reactive-dynamics benchmark may be more valuable than building the model | I-02 + field incentives | Medium |
| I-06 | The "tiny model" premise is the project's weakest claim | MLIP scaling behaviour | Medium |
| I-07 | The grid-particle extension is closer to Skala than the note implies | V-23 | High |

## Unverified claims

| ID | Claim | Why unverified | Action |
|---|---|---|---|
| U-01 | OMol25 and GMTKN55 overlap has not been excluded at graph level | No public overlap analysis found | Check before claiming any GMTKN55 result on a UMA-derived model |
| U-02 | The specific contents of the hidden ALD/CVD benchmark | Deliberately hidden | Treat all statements as inference |
| U-03 | NN-EVB, DIFFER and similar named reactive methods | Not individually checked this pass | Cite only after retrieval; see the note in [reactive potentials](../02-prior-art/07-reactive-potentials-and-enhanced-sampling-models.md) |
| U-04 | Medea and other recent TS datasets | Not checked | Omit until verified |
| U-05 | Exact challenge evaluation code/version | Not published | Ask the organisers |

## Corrections to the source note

| ID | Source note says | Record says | Where |
|---|---|---|---|
| C-01 | "The project page also advertises a multi-species demo, which is worth studying for how species are encoded" | The demo composes independently trained models; there is no species-encoding mechanism | [NCA lineage](../02-prior-art/08-neural-cellular-automata-lineage.md) |
| C-02 | Per-element networks "give no guarantee" of equal-and-opposite forces | A shared total energy guarantees it; the real defects are pair symmetry and quadratic data cost | [Element conditioning](../03-method-design/04-element-conditioning.md) |
| C-03 | SPH support radius maps to the interaction cutoff | They are different knobs: perception scale vs physical truncation | [Long range](../03-method-design/06-long-range-interactions-and-charge.md) |
| C-04 | "Training on DFT labels means the model cannot beat DFT" | More precisely: OMol25 is labelled at ωB97M-V, so it caps at that specific functional | [Critical assessment](../00-orientation/03-critical-assessment-of-the-idea-note.md) |
| C-05 | Rotation equivariance is "unclear" | The paper states it is not enforced; it is a known defect | [NCA lineage](../02-prior-art/08-neural-cellular-automata-lineage.md) |

## Numbers that are easy to get wrong

A short list for future authors, because these are the ones that keep
propagating incorrectly:

| Number | Correct value | Common error |
|---|---|---|
| Skala WTMAD-2 | 2.80 kcal/mol | Rounding to "2.5" or "3" |
| ωB97M-V on challenge board | 3.81 kcal/mol | Confusing with 3.23 (D3-corrected) |
| B3LYP on challenge board | 16.16 kcal/mol | Confusing with 6.42 (D3-corrected) |
| NPA parameters (2D) | 11k | "10k" is the paper's rounded claim; both are fine |
| Transition1x size | 9.6M configurations | "9.6M reactions" is wrong; it is 10k reactions |
| OMol25 size | >100M calculations, ~83M systems | Conflating calculations with systems |
| OMol25 level | ωB97M-V/def2-TZVPD | Saying "CCSD(T)" |
| Transition1x level | ωB97x/6-31G(d) | Saying "CCSD(T)" |
| WTMAD-2 | weighted, not plain mean | Reporting a plain mean and calling it WTMAD-2 |

> **In plain words.** Most citation errors are simple number swaps. This table
> is the antidote.

## Process for adding a claim

1. Retrieve the source. Save the page or PDF if it might change.
2. Record the exact quoted sentence and the retrieval date.
3. If it is a number, record the protocol alongside it.
4. Add a row here before using it in a document.
5. If you cannot retrieve it, do not cite it. Write "unverified" and move on.

## Open questions

- Should this log be machine-generated from citation keys? At the current size,
  manual is fine; past ~100 entries it will not be.
- Should the evidence archive include PDFs, or only HTML and checksums? HTML
  is smaller; PDFs are more faithful.

## What would change this document

- A challenge organiser publishing the evaluation protocol, which would retire
  U-02 and U-05 and confirm or refute I-01.
- A graph-level overlap analysis for OMol25 vs GMTKN55, which would retire U-01.

## Sources

Every row in the tables above names its source inline. The archived challenge
page and leaderboard payload are in
[`evidence/`](evidence/retrieval.json), with SHA-256 checksums recorded at
retrieval time.
