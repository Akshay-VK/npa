---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [../02-prior-art/04-gmtkn55-and-benchmark-mechanics.md, ../02-prior-art/03-learned-exchange-correlation-functionals.md]
---

# Provisional leaderboard

The Discovered Materials challenge publishes a provisional leaderboard of six
exchange–correlation functionals, scored on WTMAD-2 over GMTKN55, with CPU and
GPU timings. It is the only public quantitative statement of where the
speed–accuracy frontier currently sits for this problem. This document
reproduces it exactly, explains what it does and does not mean, and places the
project's own targets relative to it.

**Bottom line**

- The frontier runs from LDA at 26.35 kcal/mol and 2.4 s to ωB97M-V at
  3.81 kcal/mol and 43.5 s, on one CPU core with def2-QZVP.
- That is an 18× cost increase for a 7× error reduction. The frontier is
  expensive in exactly the region that matters.
- **The target is under 1 kcal/mol. Nothing on the board is within 3.8× of it.**
- The board appears to be evaluated **without dispersion corrections**, which
  penalises B3LYP severely and flatters ωB97M-V (which has VV10 built in). See
  [benchmark mechanics](../02-prior-art/04-gmtkn55-and-benchmark-mechanics.md).
- Two important entries are missing: r²SCAN and Skala are "being evaluated".
  Skala's own paper reports 2.80 kcal/mol, which would put it first by a wide
  margin.

## The published table

Source: [Discovered Materials, Problem 03](https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/),
retrieved 2026-11-07. Archived page and leaderboard payload in
[`09-sources/evidence/`](../09-sources/evidence/retrieval.json).

| Functional | WTMAD-2 (kcal/mol) | 95% interval | CPU s/molecule | CPU repeats | A100 s/molecule | GPU-min, full suite |
|---|---|---|---|---|---|---|
| LDA | 26.35 | 22.24–30.66 | 2.4 | 2.4–2.4 | 1.33 | 1.8 |
| PBE | 12.47 | 10.34–14.50 | 3.0 | 3.0–3.0 | 1.47 | 2.0 |
| B3LYP | 16.16 | 15.32–16.99 | 4.0 | 4.0–4.0 | 1.50 | 2.0 |
| PBE0 | 8.37 | 7.89–8.87 | 3.9 | 3.9–3.9 | 1.41 | 1.9 |
| HSE06 | 8.29 | 7.72–8.85 | 12.2 | 12.2–12.2 | 1.94 | 2.6 |
| ωB97M-V | 3.81 | 3.03–4.63 | 43.5 | 43.5–43.8 | 3.94 | 5.3 |

Protocol, as stated on the page:

- Basis set: def2-QZVP.
- Hardware: single CPU core, and separately a single NVIDIA A100.
- Each calculation repeated three times; **median** runtime reported.
- Error metric: WTMAD-2, weighted total mean absolute deviation, following
  Goerigk et al., Phys. Chem. Chem. Phys. 19, 32184 (2017).
- Reference data: GMTKN55 literature values, plus a CCSD(T) suite maintained
  by the organisers.
- Target: **under 1 kcal/mol** (chemical accuracy). Bands: 1–3 kcal/mol shown
  as "above target", >3 kcal/mol as far above.

> **In plain words.** Six methods were timed on one processor core and on one
> GPU, three times each, and scored on a public chemistry exam. The cheapest is
> 26 units wrong; the most expensive is 3.8 units wrong. The pass mark is 1.
> Nobody passes.

## Reading the frontier

### Cost scales badly

Plotting error against time reveals the shape of the problem:

| Functional | Error | Cost | Error reduction vs LDA | Cost multiple vs LDA |
|---|---|---|---|---|
| LDA | 26.35 | 2.4 s | 1.0× | 1.0× |
| PBE | 12.47 | 3.0 s | 2.1× | 1.25× |
| PBE0 | 8.37 | 3.9 s | 3.1× | 1.63× |
| HSE06 | 8.29 | 12.2 s | 3.2× | 5.1× |
| ωB97M-V | 3.81 | 43.5 s | 6.9× | 18.1× |

The first three steps are cheap and productive. The jump from PBE0 to HSE06
buys almost nothing (8.37 → 8.29) for 3× the cost. The jump to ωB97M-V buys a
lot (8.29 → 3.81) for 3.6× more. This is not a smooth frontier; it is a
staircase with one good step near the top.

*(inference)* The staircase shape is why a learned functional that reaches
~2.8 kcal/mol at semi-local cost is a genuine discontinuity rather than an
incremental improvement. It buys the ωB97M-V step without the ωB97M-V cost.

> **In plain words.** Doubling the effort usually buys a small improvement, and
> then suddenly one method is twice as good for four times the price. The
> interesting thing is to get that sudden improvement without paying.

### The GPU changes the picture less than expected

CPU to GPU speedup:

| Functional | CPU | A100 | Speedup |
|---|---|---|---|
| LDA | 2.4 | 1.33 | 1.8× |
| PBE | 3.0 | 1.47 | 2.0× |
| B3LYP | 4.0 | 1.50 | 2.7× |
| PBE0 | 3.9 | 1.41 | 2.8× |
| HSE06 | 12.2 | 1.94 | 6.3× |
| ωB97M-V | 43.5 | 3.94 | 11.0× |

The more expensive the functional, the bigger the GPU win, because the
expensive parts are the ones that parallelise. But even at 11×, ωB97M-V is
still 3× slower than PBE on GPU and still 3.8 kcal/mol from target.

*(inference)* GPU acceleration narrows the cost gap but does not change the
ordering or the accuracy ceiling. It is an implementation win, not a scientific
one.

> **In plain words.** A GPU helps the expensive methods more than the cheap
> ones, which is nice, but it does not make them more accurate. You still have
> the same wrong answer, faster.

### The dispersion distortion

B3LYP at 16.16 is the anomaly. In the literature, B3LYP-D3(BJ) scores ~6.42 on
the same benchmark ([Bonn WTMAD-2 D3 table](http://www.thc.uni-bonn.de/tc.old/downloads/GMTKN/GMTKN55/WTMAD-2-D3.html)),
and ωB97M-V with D3(BJ) scores 3.23 (Skala, Table 1). The challenge's 3.81 for
ωB97M-V is close to its dispersion-corrected value because VV10 is part of the
functional.

So the board is comparing:

- four functionals with **no** dispersion treatment, and
- one functional with **built-in** non-local correlation.

That is not a like-for-like comparison, and it explains most of the gap between
B3LYP and PBE, which reverses the usual ordering.

**What to do about it.** Do not silently "correct" the board. Report it as
published, and add a second table with a stated dispersion correction. Any
submission should state its dispersion treatment explicitly, because the
evaluators will.

> **In plain words.** One runner is wearing the right shoes and the others are
> not. That does not make the race meaningless, but you have to say so before
> comparing times.

## The missing entries

The page states: "Other common functionals, such as r²SCAN and Skala, are being
evaluated and will be added to the leaderboard."

This matters because both would change the picture:

| Missing entry | Expected position | Basis |
|---|---|---|
| **r²SCAN** | ~7.25 kcal/mol, ~PBE cost | Skala Table 1 reports 7.25 with D3(BJ) |
| **Skala-1.1** | **2.80 kcal/mol, semi-local cost** | Skala Table 1, own protocol |
| PBE-D3(BJ) | ~10.32 | Bonn table |
| ωB97M-V + D3(BJ) | ~3.23 | Skala Table 1 |

*(inference)* If Skala enters at ~2.8 with PBE-like timing, it becomes the new
frontier and the target of 1 kcal/mol looks 2.8× away instead of 3.8×. That is
still far, but it is a different problem.

> **In plain words.** The board is missing two of the most important recent
> methods. One of them is probably the best entry, and it has not been timed
> yet.

## Placing the project's targets

The project is not a functional, so it cannot enter this board. But it can
adopt the board's *scale* as an external reference. Three target levels:

| Level | Criterion | Where that sits |
|---|---|---|
| **Not embarrassing** | Match PBE accuracy at PBE cost | 12.5 kcal/mol, 3 s |
| **Interesting** | Beat ωB97M-V accuracy at PBE0 cost | <3.8 kcal/mol, <4 s |
| **Genuinely new** | Reach chemical accuracy at ≤PBE0 cost | <1 kcal/mol, <4 s |

The middle row is the realistic near-term target. The bottom row is the
challenge's bar and nobody has met it.

For a dynamics surrogate, the equivalent targets are on a different axis:

| Level | Criterion |
|---|---|
| **Not embarrassing** | Barrier MAE < 3 kcal/mol on held-out reactions |
| **Interesting** | Barrier MAE < 1.5 kcal/mol at ≥100× DFT speed |
| **Genuinely new** | Correct rates (within 2×) on a real reaction, at scale |

*(inference)* The second column is more honest for this project, because rate
accuracy is what a dynamics model is for. An NPA model that reports a WTMAD-2
number is pretending to be a functional.

> **In plain words.** We can borrow the competition's measuring stick, but we
> should not pretend to be the thing being measured. Our real test is whether
> the reaction happens at the right speed, not whether an energy table has a
> small number.

## What the board does not tell you

Eight omissions, each of which a serious reader should notice:

1. **No variance across implementations.** Three repeats measure timing noise,
   not code-to-code variation, which is often larger.
2. **No per-category breakdown.** A WTMAD-2 of 3.81 could hide a 10 kcal/mol
   barrier error offset by excellent conformer energies.
3. **No hidden-benchmark sample.** The actual scoring chemistry is not shown.
4. **No uncertainty on the error itself beyond the 95% interval**, which is
   about sampling of systems, not about the method's intrinsic error.
5. **No memory or scaling data.** Time per molecule at one size says nothing
   about $O(N^3)$ behaviour at 200 atoms.
6. **No SCF convergence statistics.** A method that fails to converge on 5% of
   molecules is not usable, and failures are usually excluded from timings.
7. **No statement of code or version.** "PBE" in one code is not identical to
   "PBE" in another.
8. **No dispersion column.** As discussed.

> **In plain words.** The table answers "how wrong and how slow" for six
> methods. It does not answer "where wrong", "how reliable", or "does it still
> work on a bigger molecule". Those are the questions a user actually has.

## Provisional means provisional

The board is labelled "Provisional", updated November 2026. Treat it as a
snapshot with three known defects — missing entries, no dispersion column, no
category breakdown — rather than as a settled ranking. When citing it:

- State the retrieval date.
- State the protocol (def2-QZVP, single core, median of 3).
- Note that r²SCAN and Skala are pending.
- Note the dispersion asymmetry.

That is enough to be honest without being tedious.

> **In plain words.** Cite it, date it, and mention what is missing. Three
> sentences of caveat turn a screenshot into evidence.

## Open questions

- What exactly does "CCSD(T) suite" on the board mean, and how does it differ
  from the GMTKN55 literature values? The page implies both are used.
- Will the organisers add a dispersion-corrected column when Skala is added?
  If Skala is evaluated with D3 and the others are not, the comparison becomes
  worse, not better.
- Is the single-core timing measured with the same integral grid and SCF
  thresholds across functionals? This is a large hidden variable.

## What would change this document

- r²SCAN and Skala appearing on the board, which would require rewriting the
  frontier analysis.
- A published evaluation protocol from the organisers, which would resolve the
  dispersion and code-version questions.
- A submission below 1 kcal/mol, which would change the entire framing of the
  project.

## Sources

1. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry*, Problem 03, updated Nov 2026.
   <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07). Page HTML and leaderboard payload archived with
   SHA-256 checksums in
   [`09-sources/evidence/retrieval.json`](../09-sources/evidence/retrieval.json).
2. Goerigk et al., *A look at the density functional theory zoo with the
   advanced GMTKN55 database*, Phys. Chem. Chem. Phys. 19, 32184 (2017).
   <https://doi.org/10.1039/C7CP04913G> (retrieved 2026-11-07).
3. Luise et al., *Skala*, arXiv:2506.14665v6, Table 1.
   <https://arxiv.org/abs/2506.14665> (retrieved 2026-11-07).
4. Grimme group, WTMAD-2 with dispersion.
   <http://www.thc.uni-bonn.de/tc.old/downloads/GMTKN/GMTKN55/WTMAD-2-D3.html>
   (retrieved 2026-11-07).
5. Rowan Benchmarks, GMTKN55 universal-potential results.
   <https://benchmarks.rowansci.com/benchmarks/gmtkn55> (retrieved 2026-11-07).
