---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: []
---

# Architecture space and the actual research question

The research question is whether local particle perception or persistent state improves the accuracy–cost trade-off for specified atomistic observables. The variants below separate these mechanisms so that a positive result can be attributed to something more precise than “NPA works for chemistry”. Everything described as a project choice is proposed; no implementation or benchmark run exists yet.

**Key takeaways**

- Build a stateless energy baseline before introducing physical-time memory.
- Separate perception, electronic-state specification, predicted quantity and propagation.
- Use the same deployment domain and data budget for comparisons.

## Model contract and state

Let $R=(r_i)$ be nuclear positions, $Z=(Z_i)$ atomic numbers, $P=(p_i)$ momenta, $m_i$ nuclear masses and $c$ the electronic-state specification plus boundary conditions. Let $h=(h_i)$ denote optional learned per-atom state. A calculator maps $(R,Z,c)$ to energy and forces; a propagator maps a phase-space state forward in physical time. A model may combine these roles, but its interface must state which one it supplies.

Specify units, supported elements, electron-count and spin conventions, periodic-cell representation, force sign, atom-index behaviour, floating-point precision and supported derivatives. Temperature normally belongs to initialisation and the thermostat. Pressure belongs to ensemble control; it is not a missing microscopic force parameter. An external electric field, however, changes the Hamiltonian and must be represented consistently. A solvent dielectric is a model assumption, not a replacement for explicitly simulated solvent.

A valid geometry input must reject impossible shapes and absent state information rather than silently guessing it. The same atomic coordinates with different electron counts can have different energies. A latent vector cannot repair a missing physical label reliably.

> **In plain words.** A photograph of a ball does not tell you its speed. Likewise atom positions are only part of a moving system. Decide which information the model receives and what answer it promises before choosing its network.

## Variants and controlled comparisons

| Family | Prediction | Persistent between physical steps? | Main question |
|---|---|---|---|
| V0 | Known analytic energy plus standard integration | No | Does the data and evaluator work? |
| V1 | Learned position/momentum increment | Optional | Can a direct propagator reproduce the declared dynamics? |
| V2 | Scalar energy; differentiated forces | No | Does particle perception help a conventional PES surrogate? |
| V3a | Energy with auxiliary variables relaxed per geometry | Numerical warm start only | Does iterative representation improve cost or accuracy? |
| V3b | Energy coupled to freely evolving latent state | Yes | Does meaningful history dependence help a defined dynamical target? |
| VX | Density-grid exchange-correlation energy | Not physical-time memory | Can particle computation improve an electronic functional? |

These identifiers are proposed project bookkeeping, not published performance categories. The published NPA architecture is a shared particle update with SPH perception; its demonstrations do not establish chemical accuracy [NPA]. Keep its graphics reproduction separate from the atomistic adaptations.

Cross each relevant family with a small set of perception choices: a radial invariant descriptor, an equivariant message-passing baseline, and SPH-style density/smoothed-feature/gradient features. Keep the energy head, optimiser, split and parameter budget fixed when testing perception. Then fix perception and test state. A full Cartesian product is unnecessary: promote only variants that answer the current gate.

> **In plain words.** Build several small vehicles with the same engine before comparing wheel designs. If you change the wheels, engine and road at once, you cannot tell what helped. A new name for a familiar vehicle does not establish a new capability.

## What memory could add

For classical nuclei on a fixed ground-state Born–Oppenheimer PES, the force is determined by geometry and the specified electronic surface. With all positions and momenta included, the ideal dynamics is Markovian. Persistent latent history is not automatically additional electronic physics.

Useful hypotheses remain: memory might amortise expensive inference; approximate a coarse-grained process with omitted degrees of freedom; represent a deliberately modelled electronic population; or improve numerical approximation at a fixed compute budget. These are different projects. Mori–Zwanzig theory motivates memory in reduced descriptions, but does not validate an arbitrary atomistic recurrent network [MEM].

The decisive counterexample is to reach the same geometry and physical state through different histories. A ground-state calculator should agree after its stated convergence procedure. If it does not, it is no longer a single-valued ground-state PES. For a genuinely history-dependent target, define which physical variable distinguishes those histories and how it is observed. **Recommendation (inference):** start with V2 and treat V3a as the first iterative extension; reserve V3b for an explicit memory hypothesis.

> **In plain words.** Remembering yesterday is useful when yesterday changes today’s answer. If the complete current situation already determines the answer, memory may just introduce confusion. Test whether two routes to the same situation produce the same prediction.

## Boundaries of a credible novelty claim

A contribution could be a faster smooth particle operator, a data-efficient representation, or a validated reduced dynamical model. “Uses particles”, “shares weights” and “learns atomic energies” already occur broadly in atomistic ML. Compare against [MLIP prior art](../02-prior-art/05-machine-learned-interatomic-potentials.md) before claiming novelty. Report latency including neighbour construction, derivatives and auxiliary iterations. A small parameter count is not a substitute for this measurement.

> **In plain words.** A recipe is new only in the part that differs from existing recipes. Name that part and compare it fairly. Count the entire cooking time, including preparation and cleanup.

## Open questions

- Which omitted variable or computation is the latent state intended to represent?
- Is the first deliverable an operator study or a chemistry model?

> **In plain words.** These are choices that the current evidence does not settle. Write down the answer before spending money on an experiment that depends on it. An empty result is better than an invented answer.

## What would change this document

- A measured advantage under the [ablation protocol](../05-evaluation/04-baselines-and-ablations.md).
- A deployment target requiring genuinely nonadiabatic or reduced dynamics.

> **In plain words.** Treat this document like a map made before the expedition. New measurements can reveal a better route. Record what changed and why when that happens.

## Sources

- [Kim et al., Neural Particle Automata, full paper v3](https://arxiv.org/html/2601.16096v3) (retrieved 2026-11-07).
- [Izvekov, Mori–Zwanzig coarse-grained dynamics](https://doi.org/10.1103/PhysRevE.104.024121) (retrieved 2026-11-07).
- [Batzner et al., NequIP](https://arxiv.org/abs/2101.03164) (retrieved 2026-11-07).
- [Batatia et al., MACE](https://arxiv.org/abs/2206.07697) (retrieved 2026-11-07).
