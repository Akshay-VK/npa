# Documentation map

The complete planned set. Numbers are stable identifiers: they appear in
filenames, in cross-links, and in the reading map. Do not renumber.

Status legend: `[ ]` not written · `[~]` drafted · `[x]` reviewed.

## 00 — Orientation

| # | Document | Purpose |
|---|---|---|
| 00.01 | `00-orientation/01-project-charter.md` | What this project is, is not, and will be judged on. Goals, non-goals, success criteria, decision rights. |
| 00.02 | `00-orientation/02-reading-map.md` | Which documents to read, in what order, for which goal (builder, scientist, reader, sceptic). |
| 00.03 | `00-orientation/03-critical-assessment-of-the-idea-note.md` | Section-by-section audit of the originating idea note: what holds, what is wrong, what is unresolved. |
| 00.04 | `00-orientation/04-what-you-need-to-know-personally.md` | The mental models, skills, and intuitions a person needs to attack this problem. Honest gap analysis. |

## 01 — Science foundations

| # | Document | Purpose |
|---|---|---|
| 01.01 | `01-science/01-electronic-structure-primer.md` | The Schrödinger equation for molecules, Born–Oppenheimer, potential energy surfaces, what a chemical reaction *is* at the electronic level. |
| 01.02 | `01-science/02-density-functional-theory.md` | Hohenberg–Kohn, Kohn–Sham, the exchange–correlation functional, Jacob's ladder, basis sets, dispersion, self-interaction error, and where DFT's reaction errors come from. |
| 01.03 | `01-science/03-wavefunction-methods-and-error-bars.md` | HF, MP2, CC, CCSD(T), CBS extrapolation, composite schemes, and the error bars on "reference" values. |
| 01.04 | `01-science/04-reaction-kinetics-and-rare-events.md` | Transition state theory, Eyring, rate constants from barriers, why reactions are rare events, and the enhanced-sampling toolbox. |
| 01.05 | `01-science/05-molecular-dynamics-and-ensembles.md` | Forces, integrators, timesteps, thermostats, barostats, ensembles, periodic boundaries, and what "trajectory" means operationally. |
| 01.06 | `01-science/06-ald-cvd-precursor-chemistry.md` | Why the challenge's hidden benchmark targets ALD/CVD precursor chemistry, and the specific chemistry involved. |
| 01.07 | `01-science/07-units-scales-and-orders-of-magnitude.md` | Every unit conversion factor and timescale the project needs, in one place. The reference card. |

## 02 — Prior art

| # | Document | Purpose |
|---|---|---|
| 02.01 | `02-prior-art/01-landscape-and-taxonomy.md` | Map of the whole field: four families of approaches to the speed–accuracy problem, and where NPA sits. |
| 02.02 | `02-prior-art/02-functional-zoo-and-jacobs-ladder.md` | LDA → GGA → meta-GGA → hybrid → double-hybrid → RPA, with representative functionals and what each rung buys. |
| 02.03 | `02-prior-art/03-learned-exchange-correlation-functionals.md` | DM21, Skala, and the neural-XC line of work. Architecture, training data, reported numbers, and open problems. |
| 02.04 | `02-prior-art/04-gmtkn55-and-benchmark-mechanics.md` | What GMTKN55 actually measures, how WTMAD-2 is computed, its known flaws, and how to read the leaderboard honestly. |
| 02.05 | `02-prior-art/05-machine-learned-interatomic-potentials.md` | Behler–Parrinello, SchNet, NequIP, MACE, Allegro and the design principles of modern MLIPs. |
| 02.06 | `02-prior-art/06-universal-potentials-and-foundation-models.md` | UMA, OMol25, eSEN, Orb, MACE-MP, MatterSim: the foundation-model wave, and what "universal" actually delivers. |
| 02.07 | `02-prior-art/07-reactive-potentials-and-enhanced-sampling-models.md` | Methods built specifically for bond breaking and long timescales: NN-EVB, Transition1x-trained models, DIFFER, Medea. |
| 02.08 | `02-prior-art/08-neural-cellular-automata-lineage.md` | NCA → Growing NCA → Particle Lenia → NPA. What the lineage actually establishes, and what NPA's own limitations section admits. |
| 02.09 | `02-prior-art/09-software-and-tooling-ecosystem.md` | The libraries, codes, and file formats the project will actually use. |

## 03 — Method design

| # | Document | Purpose |
|---|---|---|
| 03.01 | `03-method-design/01-architecture-space.md` | The full design space for an atomistic NPA, formalised. Variants 1/2/3 made precise. |
| 03.02 | `03-method-design/02-what-the-network-predicts.md` | The central fork: direct update vs energy vs hybrid. Error compounding, evaluation consequences, decision criteria. |
| 03.03 | `03-method-design/03-symmetry-equivariance-and-conservation.md` | E(3) symmetry, invariant vs equivariant features, body ordering, conservation laws, and what is lost without them. |
| 03.04 | `03-method-design/04-element-conditioning.md` | Option (a), option (b), and the hybrid. Why per-element networks break pair consistency, with the physics and the experiment that settles it. |
| 03.05 | `03-method-design/05-latent-state-and-time-mapping.md` | What the internal state should carry, how to anchor it, and how a learned step maps onto physical time. |
| 03.06 | `03-method-design/06-long-range-interactions-and-charge.md` | Cutoffs, electrostatics, Ewald summation, charge equilibration, dispersion, and learned long-range corrections. |

## 04 — Data

| # | Document | Purpose |
|---|---|---|
| 04.01 | `04-data/01-dataset-landscape.md` | Every relevant public dataset, with size, elements, level of theory, and fitness for this project. |
| 04.02 | `04-data/02-reactive-data-generation.md` | How to generate reactive trajectories: NEB, AIMD, enhanced sampling, scripted reactions, and their costs. |
| 04.03 | `04-data/03-label-fidelity-and-multifidelity.md` | The accuracy ceiling, reference hierarchies, Δ-learning, and multi-fidelity training. |
| 04.04 | `04-data/04-data-engineering-and-hygiene.md` | Formats, units, splits, leakage, deduplication, provenance, and storage. |

## 05 — Evaluation

| # | Document | Purpose |
|---|---|---|
| 05.01 | `05-evaluation/01-evaluation-design.md` | What "good" means for this project, and how to design experiments that can fail informatively. |
| 05.02 | `05-evaluation/02-metrics-and-statistics.md` | MAE, RMSE, barrier error, WTMAD-2, rollout metrics, drift, and how to report uncertainty with small samples. |
| 05.03 | `05-evaluation/03-rollout-stability-and-physics-tests.md` | The stability and physical-plausibility test battery every variant must pass. |
| 05.04 | `05-evaluation/04-baselines-and-ablations.md` | What to compare against, including null models and the ablations that isolate NPA's actual contribution. |

## 06 — Leaderboard and challenge fit

| # | Document | Purpose |
|---|---|---|
| 06.01 | `06-leaderboard/01-provisional-leaderboard.md` | The provisional leaderboard, verified, with interpretation and the missing entries. |
| 06.02 | `06-leaderboard/02-challenge-fit-analysis.md` | Exactly how far the NPA idea is from a valid submission, and the three routes to closing the gap. |
| 06.03 | `06-leaderboard/03-cost-model-and-throughput.md` | Compute cost per molecule, per step, per trajectory. What the "speed" half of the pitch must prove. |

## 07 — Delivery

| # | Document | Purpose |
|---|---|---|
| 07.01 | `07-delivery/01-roadmap-and-kill-criteria.md` | The phased roadmap, with a stop rule attached to each phase. |
| 07.02 | `07-delivery/02-experiment-protocols.md` | Concrete, runnable protocols for phases 1–4. |
| 07.03 | `07-delivery/03-reproducibility-and-infrastructure.md` | Config management, seeding, logging, artefact storage, and the determinism story. |
| 07.04 | `07-delivery/04-compute-budget-and-timeline.md` | Realistic hardware, hours, and calendar estimates. |
| 07.05 | `07-delivery/05-g0-foundations-result.md` | Execution log for G0: measured hardware limits and the first reproduction result. |
| 07.06 | `07-delivery/06-g1-g2-design-questions.md` | Design decisions for G1/G2: toy world, budget, thresholds. |
| 07.07 | `07-delivery/07-g1-g2-results.md` | G1 and G2 results: loop closes, state does not help (preliminary negative). |
| 07.08 | `07-delivery/08-g2b-results.md` | G2b results: non-conservative dynamics, state does not help. |
| 07.09 | `07-delivery/09-g2c-results.md` | G2c results: multi-particle works, perception helps, state doesn't. |
| 07.10 | `07-delivery/10-g2d-g3-plan.md` | G2d design and the three G3 running options, with the decision rule. |
| 07.11 | `07-delivery/11-g2d-results.md` | G2d results: state carries partial phase information but does not beat the stateless baseline reliably. |
| 07.12 | `07-delivery/12-g3-results.md` | G3 results: distance-MLP trained on CCSD(T)/cc-pVDZ passes the H + H₂ barrier, invariance and 20 Å dissociation gate; MP2 control fails. |

## 08 — Risk

| # | Document | Purpose |
|---|---|---|
| 08.01 | `08-risk/01-risk-register.md` | Every risk in the source note plus those it missed, scored, with mitigation and owner. |
| 08.02 | `08-risk/02-failure-modes-catalogue.md` | The physics and machine-learning failure modes, with symptoms and diagnostics. |

## 09 — Sources

| # | Document | Purpose |
|---|---|---|
| 09.01 | `09-sources/01-annotated-bibliography.md` | Every source used, annotated with why it matters and how much to trust it. |
| 09.02 | `09-sources/02-verification-log.md` | Claim-by-claim record of what was checked against a primary source, and what could not be. |

## ADRs

| # | Decision |
|---|---|
| 0001 | Documentation is a primary artefact, not an afterthought |
| 0002 | Research project first; challenge submission is an option, not the goal |
| 0003 | Energy-based hybrid as the target architecture |
| 0004 | Synthetic data before real chemistry |
| 0005 | Shared trunk with element conditioning over per-element networks |
