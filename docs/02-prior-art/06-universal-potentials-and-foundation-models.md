---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: [05-machine-learned-interatomic-potentials.md]
---

# Universal potentials and foundation models

Between 2023 and 2026 the MLIP field shifted from "one model per chemistry" to
"one model for most of the periodic table". These universal potentials are now
the default starting point for any new atomistic ML project, which makes them
both the project's strongest baseline and its most likely competitor. This
document separates what "universal" actually delivers from what it promises.

**Bottom line**

- OMol25 is the largest molecular dataset: **more than 100 million DFT
  calculations at ωB97M-V/def2-TZVPD**, 83 elements, systems up to 350 atoms,
  roughly 83 million unique systems.
- UMA is trained on OMol25 plus other Meta FAIR datasets, and is the strongest
  openly available general-purpose potential.
- On GMTKN55, the best universal potentials reach **~3.75 kcal/mol WTMAD-2** —
  comparable to ωB97M-V — while materials-trained potentials such as
  MACE-MP-0 score **~31.5**, catastrophically worse.
- This is distillation, not surpassing: UMA learns from ωB97M-V-labelled data,
  so it cannot be more accurate than ωB97M-V on the same observables.
- The gap that matters is **barriers**, where universal potentials lag well
  behind the best hybrids.

## The datasets

### OMol25

Levine et al., *The Open Molecules 2025 (OMol25) Dataset, Evaluations, and
Models*, [arXiv:2505.08762](https://arxiv.org/abs/2505.08762) (retrieved
2026-11-07).

| Property | Value |
|---|---|
| Size | >100 million DFT calculations |
| Unique systems | ~83 million |
| Level of theory | ωB97M-V / def2-TZVPD |
| Elements | 83 |
| Max system size | 350 atoms |
| Content | Small molecules, biomolecules, metal complexes, electrolytes, explicit solvation, variable charge/spin, conformers, **reactive structures** |
| Compute | "billions of CPU core-hours" |

The size is the headline. The composition is more interesting: OMol25
deliberately includes the awkward cases — charged species, open shells,
solvated systems, and reactive geometries — that earlier datasets avoided. That
makes it a much better pretraining corpus for a reaction model than, say, QM9
or MD17.

Two caveats that are easy to miss:

1. **The labels are ωB97M-V, not CCSD(T).** ωB97M-V is a range-separated
   hybrid with VV10, and it is the best functional on the challenge leaderboard
   at 3.81 kcal/mol. Training on OMol25 therefore caps you at reproducing a
   functional that is itself ~3.8× above chemical accuracy.
2. **The dataset is DFT, not experiment.** Errors in ωB97M-V are systematic,
   and a model trained on it will inherit them faithfully.

### Other universal datasets

| Dataset | Size | Domain | Level |
|---|---|---|---|
| OMat24 | ~110M | Inorganic materials | PBE/PBE+U (mixed) |
| OC20 / OC22 | ~1M / ~0.5M | Catalysis surfaces | RPBE / PBE |
| Alexandria | ~50M | Periodic materials | PBE |
| Transition1x | 9.6M | Organic reactions | ωB97x/6-31G(d) |
| SPICE | ~1M | Drug-like molecules, dimers | ωB97M-D3(BJ) |
| QM9 | 134k | Small organics | B3LYP |

*(inference)* The pattern is that molecular chemistry is labelled at hybrid
quality and materials chemistry at GGA quality, because materials are far more
expensive per calculation. A universal model therefore has a quality cliff
between its molecular and materials halves.

> **In plain words.** The biggest dataset covers most of the periodic table but
> was labelled by a method that is good, not perfect. Everything the model
> learns is bounded by that method's mistakes.

## UMA and its competitors

UMA ("Universal Model for Atoms") is Meta FAIR's model trained across OMol25
and the other datasets above. The architectural idea is a mixture of experts
with task-specific heads, so that one model can serve molecular, materials, and
catalytic tasks without them fighting each other.

The competing universal models, in rough order of current relevance:

| Model | Origin | Strength | Weakness |
|---|---|---|---|
| **UMA** | Meta FAIR | Broadest molecular coverage; strong on OMol25 tasks | Heavy; licence and deployment constraints |
| **eSEN** | Meta FAIR (OMol25 paper) | Conserving, competitive with UMA | Less widely deployed |
| **MACE-MP-0 / 0b2** | Cambridge | Excellent for materials | Poor on molecular thermochemistry |
| **MatterSim** | Microsoft | Materials, broad elements | Molecular chemistry weaker |
| **Orb** | Orbital Materials | Fast, materials-focused | Molecular accuracy lags |
| **CHGNet / M3GNet** | Earlier generation | Cheap, well-known | Superseded on accuracy |
| **SevenNet** | KAIST | Scalable | Narrower evaluation |

*(inference)* For a molecular reaction project, the relevant comparison is UMA
and eSEN. MACE-MP-0 is a materials model and should not be used as a molecular
baseline; doing so would produce a flattering and dishonest comparison.

> **In plain words.** "Universal" models are universal in *coverage*, not in
> *quality*. A model trained mostly on crystals is bad at molecules, and using
> it as your baseline would make your method look better than it is.

## The benchmark reality

Rowan Benchmarks evaluates MLIPs on GMTKN55, which is unusual and valuable
because most MLIP papers do not
([benchmarks.rowansci.com/benchmarks/gmtkn55](https://benchmarks.rowansci.com/benchmarks/gmtkn55),
retrieved 2026-11-07). Reported WTMAD-2 values:

| Model | Small | Large | Barriers | Intra NCI | Inter NCI | **All** |
|---|---|---|---|---|---|---|
| UMA Medium 1.1 (OMol task) | 3.07 | 3.86 | 3.02 | 5.05 | 2.46 | **3.75** |
| eSEN Conserving Small | 3.08 | 3.46 | 2.95 | 5.29 | 2.83 | **3.86** |
| UMA Small 1.2 (OMol task) | 2.95 | 3.73 | 2.77 | 5.24 | 2.94 | **3.87** |
| MACE-MP-0b2 (Large) | 32.15 | 26.26 | 14.01 | 37.68 | 34.49 | **31.54** |
| Orb-d3-v2 | 20.69 | 14.44 | 18.17 | 47.47 | 33.73 | **32.41** |
| MACE-MP-0 (Large) + D3BJ | 29.55 | 34.75 | 26.23 | 41.14 | 22.99 | **32.45** |

Protocol notes, because they matter:

- Rowan exposes **six WTMAD variants**; the values above are for its default
  selection. Do not compare them to a WTMAD-2 computed elsewhere without
  checking the variant.
- GMTKN55 references are CCSD(T)-based; UMA was trained on ωB97M-V data. Some
  of the agreement may be inherited rather than learned.
- Overlap between OMol25 and GMTKN55 has not been systematically excluded at
  the molecular-graph level in the way Skala does. *(unverified)*
- These are not the challenge's protocol (def2-QZVP, single core). They are
  single-point evaluations using each model's own settings.

**Three readings.**

1. **Universal potentials are competitive on overall WTMAD-2.** UMA at 3.75 is
   essentially level with ωB97M-V's 3.81 on the challenge board. On this
   benchmark, the "MLIPs can't do thermochemistry" story is out of date.
2. **Materials-trained models are catastrophic.** MACE-MP-0 at 31.5 is not a
   slightly worse model; it is a different chemistry. This is the clearest
   demonstration that coverage is not transfer.
3. **Barriers remain the weak point.** UMA's barrier score (3.02) is barely
   better than its overall score (3.75), whereas the best hybrids are strongest
   on barrier subsets — Skala's Table 1 shows ωB97M-V at 1.13–1.33 kcal/mol on
   BH76 and BHDIV10. Aggregation differs, so treat this as suggestive rather
   than exact, but the pattern is consistent with everything else in the
   literature: equilibrium data does not teach barrier physics.

> **In plain words.** The best universal models now match the best hand-built
> methods on a broad chemistry exam. But they are still much worse at the one
> thing this project cares about — how high the hill is.

## Cost

Universal potentials are cheap relative to DFT and expensive relative to small
MLIPs:

- A forward pass for a 50-atom molecule is milliseconds on a GPU, versus
  seconds to minutes for DFT.
- Memory scales with the number of neighbours and the number of tensor
  channels; large models need a modern GPU.
- Throughput is typically thousands to millions of configurations per GPU-hour,
  depending on model size and system size.

*(inference)* The practical implication is that a small NPA model cannot
compete on accuracy per parameter with UMA, but might compete on
configurations-per-second for a narrow chemistry. That is a real, measurable
axis, and it is the one the project should claim if it claims anything.

> **In plain words.** These models are fast enough to run simulations that were
> impossible five years ago, and slow enough that a truly tiny model would
> still be interesting if it were accurate.

## Build on top, or beside?

Three strategies, with a recommendation.

**A. Fine-tune UMA on the target chemistry.** Cheap, likely accurate, and
almost certainly the strongest baseline. It also makes the project a
fine-tuning study rather than an architecture study.

**B. Build a small model beside it.** Higher risk, but the only route to a
genuine architectural claim. Requires beating UMA on cost *and* being
competitive on the target observables.

**C. Use UMA as a teacher.** Distil its predictions into the small model, then
correct toward higher-fidelity labels. This is a legitimate multi-fidelity
strategy and probably the most efficient use of a large model in a small
project.

**Recommendation:** run A as a baseline in week one, because it is cheap and it
sets the bar. Pursue B for the research claim. Consider C if B's data
requirements turn out to be the binding constraint. This is recorded in
[ADR 0003](../adr/0003-energy-based-hybrid.md) as context for the architecture
decision.

> **In plain words.** Do the boring thing first: fine-tune the big model and
> see how good it gets. That number is the bar. Then try to beat it with
> something small. If you cannot, distil the big model into the small one and
> at least get the speed.

## What universal potentials do not solve

- **Reaction barriers.** As above.
- **Long-timescale dynamics.** A fast potential still needs $10^{12}$ steps to
  see a millisecond event.
- **Transition-metal reaction chemistry.** Coverage exists; accuracy is much
  weaker than for main-group.
- **Charge and spin state selection.** OMol25 includes variable charge/spin,
  but predicting *which* state is lowest is a different problem.
- **Uncertainty.** Most universal models do not ship calibrated uncertainty.

These gaps are the project's opportunity, and each one is a candidate research
question. The strongest is the first: a potential that gets barriers right at
small-model cost is a real contribution.

> **In plain words.** The big models solved coverage and speed. They did not
> solve the hill heights, the long wait for rare events, or knowing when they
> are wrong. Those are still open.

## Open questions

- How much of UMA's GMTKN55 performance is memorisation of ωB97M-V training
  data? A graph-level overlap analysis would settle it.
- Does fine-tuning UMA on Transition1x close the barrier gap? This is a
  one-week experiment and should be run before any architecture work.
- What is the smallest model that retains UMA-level barrier accuracy on a
  narrow chemistry? That number defines the project's target.

## What would change this document

- A universal potential that matches hybrid accuracy on barrier heights, which
  would make the reactive-surrogate niche much narrower.
- Release of a much larger high-accuracy molecular dataset (CCSD(T)-level at
  OMol25 scale), which would change every accuracy ceiling in this project.
- A licensing change that makes UMA unusable for research, which would shift
  the baseline to eSEN or MACE.

## Sources

1. Levine et al., *The Open Molecules 2025 (OMol25) Dataset, Evaluations, and
   Models*, arXiv:2505.08762. <https://arxiv.org/abs/2505.08762> (retrieved
   2026-11-07).
2. Rowan Benchmarks, GMTKN55 results for UMA, eSEN, MACE-MP-0, Orb.
   <https://benchmarks.rowansci.com/benchmarks/gmtkn55> (retrieved 2026-11-07).
3. Meta FAIR, OMol25 and UMA announcement.
   <https://ai.meta.com/blog/meta-fair-science-new-open-source-releases/>
   (retrieved 2026-11-07).
4. Luise et al., *Skala*, arXiv:2506.14665v6, Table 1.
   <https://arxiv.org/abs/2506.14665> (retrieved 2026-11-07).
5. Batatia et al., *A foundation model for atomistic materials chemistry*
   (MACE-MP-0), arXiv:2401.00096.
   <https://arxiv.org/abs/2401.00096> (retrieved 2026-11-07).
