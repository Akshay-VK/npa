---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [02-verification-log.md, 04-data/01-dataset-landscape.md]
---

# Evaluation design

What "good" means for this project, and how to design experiments that can
fail informatively. This document specifies the observable hierarchy, the
baseline set, and the experiment structure so that every result answers a
well-defined question.

**Bottom line**

- The project evaluates on **three observable tiers**: single-point energy,
  barrier height, and rate constant. Each implies a different model and
  benchmark.
- The **baseline set** includes four reference points: PBE (cheap), ωB97M-V
  (accurate), Skala-1.1 (learned functional), and B3LYP-D3(BJ) (dispersion
  sanity check). Every result ships with all four.
- The **decision structure** is the roadmap's phase gate: G0 → G1 → G2 → G3 → G4.
  An experiment that does not map to a gate is a distraction.
- The **metric template** is in [metrics and statistics](../05-evaluation/02-metrics-and-statistics.md).
  Every result must fill that template.

## The observable hierarchy

Three things the project can predict, ordered from easiest to hardest:

| Tier | Observable | What it requires | Why it matters |
|---|---|---|---|
| **1. Single-point energy** | The PES at a configuration | Energy difference vs reference | Fundamental; every model must do this. |
| **2. Barrier height** | The electronic (or free) barrier between reactant and product | Energy along a reaction path, especially the saddle | This is what the challenge scores. A model can be good at tier 1 and bad at tier 2. |
| **3. Rate constant** | The reaction speed, from barrier + prefactor | Barrier + ZPE + entropy + tunnelling + recrossing | This is what chemistry is actually about. A model can be good at tiers 1–2 and bad at tier 3. |

**Decision rule.** The project must decide which tier is the primary evaluation
observable before phase 3. If the project says "we predict rates" but only reports
barrier MAE, that is a mismatch. If the project says "we predict energies" and
never reports barriers, the model has not been stress-tested.

> **In plain words.** You cannot evaluate a dynamics model on energies alone.\n> You need to decide: am I energy, barrier, or rate? Pick one as the primary\n> metric, and report the others as secondary.

## The baseline set

Every result must include these four references, reported with the same protocol:

| Baseline | WTMAD-2 (kcal/mol) | Barrier MAE (kcal/mol) | Time / mol (s) | Notes |
|---|---|---|---|---|
| **PBE** | 12.47 (leaderboard) | 2–3 (typical on BH76) | 3 (challenge) | Cheap workhorse; no dispersion. |
| **ωB97M-V** | 3.81 (leaderboard) | 1.1–1.3 (BH76 etc.) | 43.5 (challenge) | Best functional; has VV10 dispersion. |
| **Skala-1.1** | 2.80 (own eval, D3(BJ)) | N/A (not barrier-optimized) | ~10 s (extrapolated) | Learned functional, semi-local cost. |
| **B3LYP-D3(BJ)** | ~6.42 (Bonn table) | 1.5–2.0 (typical) | 4.0 (challenge) | Catches "forgot dispersion" errors. |

**Protocol notes.**

- WTMAD-2: challenge protocol (def2-QZVP, no dispersion column for the leaderboard;
  D3(BJ) added per Bonn table for Skala and B3LYP-D3(BJ)).
- Barrier MAE: BH76 + BHDIV10 + BHPERI + INV24 + PX13 + WCPT18, vs CCSD(T).
- Time: single CPU core, def2-QZVP, median of 3. NPA model should report its
  own hardware/software stack.

> **In plain words.** Every result has four reference points. If you beat PBE
> on accuracy and cost, you have a point. If you beat ωB97M-V on accuracy at
> lower cost, you have a stronger point. If you beat Skala, you have a claim.
> More than that and you are overfitting.

The baseline set is the project's commitment to honest comparison. No result is
published without all four numbers filled in.

## The experiment cycle

Each experiment follows this template:

| Step | Action | Output |
|---|---|---|
| **1. Hypothesis** | A testable claim, mapped to a roadmap gate. | Gate reference (G0–G4). |
| **2. Data split** | Defined train/test split, with provenance. | Data manifest, checksum. |
| **3. Training** | Single run, fixed seeds, logged config. | Checkpoint, training log. |
| **4. Evaluation** | Metric template filled, baseline set included. | Results table. |
| **5. Diagnosis** | Stability envelope, rotation test, ablation. | Diagnosis report. |
| **6. Gate decision** | Pass/fail against the gate's kill criterion. | Go/no-go decision. |

**No experiment proceeds without a mapped gate.** If the experiment's question
does not align with G0–G4, it is a distraction and should be dropped.

## Gate alignment

| Gate | Primary experiment question | Required observables |
|---|---|---|
| **G0** (Foundations) | Can we run the code? | Setup checklist. |
| **G1** (Toolchain) | Does the loop close on synthetic data? | Energy drift, barrier MAE, rate estimate. |
| **G2** (Decision) | Does persistent state help? | Barrier MAE comparison (endpoint vs force loss). |
| **G3** (One real reaction) | Does it survive real electronic structure? | Barrier MAE vs reference, rotational invariance, dissociation. |
| **G4** (Organic chemistry) | Is it competitive with baselines? | Barrier MAE on held-out reactions, cost per trajectory. |
| **G5** (Optional) | Is there a story? | Free-energy profile, rate comparison. |

## Error reporting template

Every result must report:

1. **The primary metric** (chosen from the observable hierarchy), with value and
   95% confidence interval (or, for small seed counts, a seed-by-value table).
2. **The three secondary metrics** (the other two tiers), with values.
3. **The baseline set** values (four numbers), so the reader can place the result.
4. **The protocol** for each number: basis set, reference level, dispersion
   treatment, hardware, software version, seed count.
5. **The failure modes** observed, drawn from the [physics test battery](../05-evaluation/03-rollout-stability-and-physics-tests.md).

> **In plain words.** The template is the contract. If you do not fill every
> column, the result is incomplete. This is not mean; it is how science works.

## What would change this document

- A published evaluation protocol from the challenge organisers, which would
  retire several "protocol assumed" notes.
- Evidence that the observable hierarchy can be reduced without losing
  information, which would simplify the experimental design.
- A new primary observable (e.g. free-energy profile) that the project decides
  to adopt, which would require a document rewrite.

## Open questions

- Which tier should be the primary observable for the project? The answer
  depends on the architecture choice (energy-based vs direct-update). This
  should be decided in phase 1 and recorded in the gate log.
- How many seeds are enough? The contract says pre-register the effect size
  and compute the number of seeds needed. For now, ≥5 is the target.
- Should the barrier MAE be reported on BH76 alone, or on the full set of
  7 barrier subsets? The full set is more informative; BH76 alone is simpler.

## What would change this document

- A published evaluation protocol from the challenge organisers, which would
  retire several "protocol assumed" notes.
- Evidence that the observable hierarchy can be reduced without losing
  information, which would simplify the experimental design.
- A new primary observable (e.g. free-energy profile) that the project decides
  to adopt, which would require a document rewrite.

## Sources

1. Goerigk et al., *A look at the density functional theory zoo with the
   advanced GMTKN55 database*, Phys. Chem. Chem. Phys. 19, 32184 (2017).
   <https://doi.org/10.1039/C7CP04913G> (retrieved 2026-11-07).
2. Grimme group, WTMAD-2 with and without dispersion.
   <http://www.thc.uni-bonn.de/tc.old/downloads/GMTKN/GMTKN55/WTMAD-2-D3.html>
   (retrieved 2026-11-07).
3. Bryenton and Johnson, *WTMAD-4: A Fair Weighting Scheme for GMTKN55*,
   arXiv:2509.23498. <https://arxiv.org/abs/2509.23498> (retrieved 2026-11-07).
4. Schreiner et al., *Transition1x*, Scientific Data 9, 2022.
   <https://www.nature.com/articles/s41597-022-01870-w> (retrieved 2026-11-07).
5. Levine et al., *OMol25*, arXiv:2505.08762. <https://arxiv.org/abs/2505.08762> (retrieved 2026-11-07).
6. Eyring, *The activated complex in chemical reactions*, J. Chem. Phys. 3,
   107 (1935). <https://doi.org/10.1063/1.1749604> (retrieved 2026-11-07).
7. Luise et al., *Skala*, arXiv:2506.14665v6. <https://arxiv.org/abs/2506.14665> (retrieved 2026-11-07).
8. Kim et al., *Neural Particle Automata*, arXiv:2601.16096. <https://arxiv.org/abs/2601.16096> (retrieved 2026-11-07).