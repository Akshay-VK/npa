# Neural Particle Automata for Atomistic Reaction Dynamics

*Early-stage idea note · 6 Nov 2026 · SEDS Simulations*

## 1. The idea in one paragraph

Neural Particle Automata (NPA) are a recent particle-based generalisation of Neural Cellular Automata: every particle has a continuous position and a learned internal state, and a single shared neural rule updates both. The published work tests this on graphics-style tasks. The idea here is to point the same machinery at chemistry instead: treat each particle as an **atom**, train on **time series of chemical reactions**, then set an initial configuration and let the learned rule roll the system forward. Two ways of telling atoms apart are on the table: (a) one network with a fixed per-atom parameter carrying element identity (plus things like orientation), or (b) a separate network per element, each optimising itself. Beyond positions, the model would need extra conditioning such as energy levels and environmental conditions.

The motivation is the speed–accuracy barrier in quantum chemistry: cheap methods are not accurate enough for reactions, and accurate methods are too expensive to run at scale.

**Short version of my assessment:** the core intuition (a tiny, local, shared rule that is cheap to run) is genuinely attractive, and the idea is worth a toy-scale test. But three things need sorting out early: the challenge page asks for something different from a dynamics surrogate (Section 2), the biggest design decision is *what the network predicts* rather than a-versus-b (Section 5), and option (b) has a structural problem (Section 6).

## 2. The problem this is aimed at, and where the idea fits

The Discovered Materials challenge (Problem 03, listed as open, updated Nov 2026) is framed as reaction prediction before the lab. DFT is fast but often inaccurate for reactions; coupled-cluster methods are accurate but impractical at scale. The stated task is narrower than the framing: **develop a more accurate exchange-correlation functional that improves DFT without sacrificing efficiency.**

Submissions are judged on a hidden benchmark of reaction energies, activation barriers, binding energies and bond dissociation energies for atomic layer deposition and chemical vapour deposition precursor chemistry. Entrants must supply a method description, runnable code, and results on the public GMTKN55 benchmark. Scoring covers error, compute time per molecule, and reproducibility.

The provisional leaderboard (WTMAD-2 error, single CPU core, def2-QZVP basis) shows the shape of the trade-off:

| Functional | Error (kcal/mol) | CPU time per molecule |
| --- | --- | --- |
| LDA | 26.35 | 2.4 s |
| PBE | 12.47 | 3.0 s |
| B3LYP | 16.16 | 4.0 s |
| PBE0 | 8.37 | 3.9 s |
| HSE06 | 8.29 | 12.2 s |
| ωB97M-V | 3.81 | 43.5 s |

The stated target is under 1 kcal/mol (chemical accuracy). For context, Microsoft's learned functional Skala reports 2.8 kcal/mol on GMTKN55 at roughly semi-local DFT cost, so a neural approach to this problem already exists and is a serious baseline.

**Where the NPA idea fits.** It attacks the same underlying bottleneck (accurate reaction chemistry is expensive) from a different side. It would be a *learned dynamics surrogate*, closer to a reactive machine-learned interatomic potential than to a functional. That means:

- As framed (time evolution from an initial state), it is **not directly a challenge submission**, because there is no functional to plug into DFT and no single-point barrier to score.
- If the model is built around an energy (Section 5, variants 2 and 3), barriers and reaction energies can be extracted and compared against the same kinds of numbers the benchmark uses. That makes it benchmark-adjacent.
- A more direct bridge to the challenge is the speculative extension in Section 11.

I would treat the challenge as inspiration and a yardstick, and decide deliberately whether the goal is a submission or a research and blog project.

## 3. What NPA is, and what it is not yet

From the paper (Kim, Pajouheshgar, Süsstrunk, Jakob, Park; arXiv 2601.16096, Jan 2026):

- NPA is a Lagrangian counterpart to grid-based NCA: cells become particles with continuous position and internal state, both updated by one shared learnable rule.
- Perception is done with differentiable Smoothed Particle Hydrodynamics (SPH) operators instead of convolutions, backed by CUDA kernels so that neighbour interactions scale to many particles.
- The rule can be very small; the authors note networks with as few as ten thousand parameters.
- Reported tasks are morphogenesis (growing shapes), point-cloud classification, and particle-based texture synthesis, with NCA-style robustness and self-regeneration retained. (Worth noting: the paper does not do image reconstruction as such; texture synthesis is the closest.)
- The paper highlights that particle formulations allow heterogeneous dynamics and concentrate compute where activity is happening. The project page also advertises a multi-species demo, which is worth studying for how species are encoded.

**What it does not give you out of the box** (my reading; check against the code):

- No built-in energy, forces, or conservation laws. The rule is a learned update, not a derivative of a potential.
- No guarantee of rotation equivariance. SPH uses relative positions, so translation invariance is natural, but whether the update treats rotations consistently depends on how gradient features enter the network.
- Steps are learned iterations, not physical time. Nothing ties one step to a femtosecond.
- Every task so far is a *target-shape* problem, not a *match-a-physical-trajectory* problem. The training signal for chemistry is of a different kind.

## 4. Mapping NPA onto atoms

| NPA concept | Atomistic counterpart | Comment |
| --- | --- | --- |
| Particle position | Atomic coordinates | Direct. Units and scale need care. |
| Internal state vector | Latent per-atom electronic variables (partial charge, spin, bond-order-like channels) | This is where NPA offers something plain interatomic potentials lack: persistent hidden state. |
| SPH neighbourhood and support radius | Interaction cutoff | Bonding is short-range; electrostatics and dispersion are not. |
| Shared rule | One model for all atoms | Natural fit for chemistry's locality, with the caveats in Section 6. |
| One update step | A molecular-dynamics time step | Must be defined; see Section 5. |
| Species | Element identity | The a-versus-b decision. |

## 5. The central fork: what does the network predict?

This decision matters more than a-versus-b, because it determines what you can evaluate and how badly errors compound.

**Variant 1: direct update (neural integrator).** The rule outputs position and state changes each step, as in the original NPA. Simplest and closest to the paper; likely the fastest. Downsides: no energy, so no barriers; energy drift and error accumulation over long rollouts; hard to compare against any benchmark except trajectory similarity.

**Variant 2: energy-based.** An NPA-style local network outputs a per-atom energy, forces come from automatic differentiation, and a standard integrator moves the atoms. This is essentially a machine-learned interatomic potential with an NPA-flavoured architecture. Conservative by construction, gives reaction energies and barriers (via transition-state search), and is benchmarkable. It departs from the pure automaton spirit.

**Variant 3: hybrid.** Energy-based dynamics as in Variant 2, plus a persistent per-atom latent state that evolves under an NCA-style learned rule and feeds back into the energy. This keeps what is distinctive about NPA (hidden state, local rule) while staying physically grounded, and is where I would aim.

**Suggested path:** use Variant 1 for the cheapest toy experiments (Section 10, phases 1 and 2), then move to Variant 3 for anything touching real chemistry.

**Time-step and rare-event issues apply to all variants.** Atoms vibrate on femtosecond timescales while reactions can take far longer, so most trajectories contain no reactive event. A step-by-step surrogate trained on ordinary trajectories will barely see bond breaking. Training data must be biased toward reactive regions (Section 8).

## 6. Your two options compared

### (a) One network, element identity as a fixed per-atom parameter

This is the standard approach in modern interatomic potentials and matches the shared-rule philosophy of NCA. Parameters are shared across elements, so chemically similar elements can borrow statistical strength, and adding an element means adding an embedding rather than a network. Two refinements:

- Make identity a **learned embedding of atomic number**, optionally concatenated with fixed physical descriptors (electronegativity, covalent radius, valence electron count). That gives the network a smooth notion of chemical similarity.
- Do **not** treat orientation as a fixed parameter. Orientation is a property of the geometry, so it should come from relative positions (ideally through an equivariant formulation). What *can* be dynamic and per-atom are latent electronic channels, which belong in the internal state.

### (b) One network per element

The intuition (each element optimises itself and ignores the others) breaks down for a physical reason: **elements never act alone.** An O–H interaction has to be modelled consistently from both atoms' sides, and the forces must be equal and opposite. Independently trained networks give no guarantee of this, so you get inconsistent pair interactions, double counting, and drift. Practical problems follow: N networks for N elements, sparse data for rare elements, and a coupled, non-stationary training problem rather than the clean independence the idea hopes for.

The truth in (b) is that elements do have different needs. A middle ground captures it:

- a **shared trunk** with **per-element output heads or small adapters**, or
- conditioning on the **pair** of elements (Z\_i, Z\_j) in the interaction layer.

### Verdict

|  | (a) Shared + embedding | (b) Per-element networks | Hybrid: shared trunk + per-element heads |
| --- | --- | --- | --- |
| Pair consistency | Natural | Not guaranteed | Natural |
| Data efficiency | Best | Worst for rare elements | Good |
| Scales to many elements | Yes | Poorly | Yes |
| Matches NPA's shared-rule premise | Yes | No | Mostly |
| Role in this project | Default | Ablation baseline on H, C, O only | Second experiment |

A clean experiment is cheap to run on a toy system (Section 10): compare all three on the same two-species data and let the results decide.

## 7. Conditioning inputs

The instinct to supply extra parameters is right, but they should be split by what they are:

- **Global, fixed per system:** total charge, spin multiplicity, temperature, pressure, solvent or dielectric environment, external field. Inject them as broadcast conditioning (for example feature-wise modulation) on every atom.
- **Per-atom, dynamic:** partial charges, spin density, hybridisation-like descriptors. Keep them as latent internal-state channels, and where reference data exists, add auxiliary losses so they are anchored to something physical.
- **Temperature properly belongs in the dynamics.** It enters through initial velocities and a thermostat (for example Langevin) around the learned model, not only as an input number.
- **"Energy levels" is ambiguous.** If it means orbital or electronic-state energies, that is hard to supply as an input and better treated as an auxiliary prediction target. If it means total system energy, that points to Variants 2 and 3.

A caution: with small datasets, every extra input is another route to overfitting. Start with a fixed temperature and neutral singlet systems, and add conditioning one factor at a time.

## 8. Data: the real bottleneck

The model needs reactive, time-resolved, high-accuracy data, and that combination is scarce.

- **Transition1x** has 9.6 million DFT energy and force calculations on and around reaction pathways for about 10,000 organic reactions (H, C, N, O), generated with the nudged elastic band method. Excellent for transition-state regions, but these are path-optimisation iterates, not real-time dynamics.
- **OMol25 and UMA (Meta, 2025)** offer over 100 million DFT snapshots of molecules with up to 350 atoms across most of the periodic table, plus a pretrained universal interatomic potential. Valuable for pretraining or as a strong baseline; again mostly configurations rather than reaction time series.
- **Ab initio molecular dynamics** is the source of true time series, but it is expensive and rarely reactive at ordinary temperatures. Options: higher temperatures, enhanced sampling, or scripted reactive setups.
- **Accuracy ceiling.** Training on DFT labels means the model cannot beat DFT. The challenge's whole point is going beyond it. Closing that gap needs coupled-cluster-level references (rare and costly) or a multi-fidelity scheme: a cheap model corrected toward a small set of high-accuracy labels. Skala's authors attribute much of their progress to an unusually large volume of high-accuracy reference data, which signals how central data is.

This is the main reason to begin on synthetic data where the ground-truth dynamics are free.

## 9. Evaluation

Two tracks, depending on the variant:

- **Energy-based variants:** reaction energies and barrier heights against reference values; compute time per molecule on the same footing as the leaderboard; comparison against UMA or another pretrained potential as a baseline.
- **All variants:** rollout fidelity (RMSD against reference trajectories over increasing horizons), bond-length and angle distributions, energy drift or conservation, whether reactive events occur at roughly the right rate, and stability on held-out molecules and unseen element combinations.

Report accuracy and speed together, because the project's pitch is the trade-off, not either number alone.

## 10. Roadmap

Each phase should be able to fail cheaply and tell you something.

1. **Reproduce NPA.** Run the public implementation and the multi-species demo; understand how species and state are encoded and what the SPH settings do.
2. **Toy world.** Two-species particles in 2D with a known pair potential (Lennard-Jones or Morse style). Generate trajectories with a classical integrator. Compare Variant 1 and Variant 3, and options (a), (b) and the hybrid, on rollout error and drift. This is the cheapest way to settle the design fork.
3. **Simplest real reaction.** The hydrogen exchange reaction H + H₂ has a small, well-studied energy landscape, so ground truth is accessible. Check that the model finds the barrier.
4. **Small organic reactions.** A subset of Transition1x (H, C, N, O only), with hybrid heads and a first set of global conditioning inputs. Compare against a pretrained potential.
5. **Conditioning and accuracy study.** Add temperature, charge and spin one factor at a time; try a multi-fidelity correction toward a small high-accuracy set.
6. **Decide:** write-up and blog post, or a challenge-style submission (Section 11).

A useful stop rule: if Phase 2 shows no advantage from NPA-style hidden state over a plain local network, the idea's distinctive claim is in trouble, and it is better to learn that in weeks than months.

## 11. Speculative extension: grid points as particles

The challenge asks for a functional, and Skala's published approach gains accuracy by learning non-local interactions between points on the integration grid rather than relying on hand-built features. That structure (points in space, each with local features, exchanging information with neighbours) resembles a particle system. An NPA-like architecture where the *particles are grid points* carrying density features could be an interesting way to produce an exchange-correlation energy, and would plug straight into DFT, matching the challenge format. This is purely a hypothesis, and it requires a DFT code you can modify and a large body of high-accuracy training data, so it is a later-stage option, not a starting point.

## 12. Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Rollout error compounds | One-step accuracy does not imply stable long trajectories | Train with multi-step rollouts; use Variant 2 or 3 |
| No reactive events in data | The model never sees bonds break | Transition1x-style path data, high temperature, enhanced sampling |
| Short-range locality | Misses electrostatics and dispersion | Learned charges plus a long-range correction term |
| Not rotation-equivariant | Same molecule, different orientation, different answer | Equivariant features, or augmentation as a stopgap |
| Accuracy ceiling set by labels | Cannot beat the method that produced the data | Multi-fidelity training with a small high-accuracy set |
| Compute and data cost | Real DFT labels are expensive | Begin on synthetic data; reuse public datasets |
| Crowded field | Strong learned potentials and functionals already exist | Pick the niche (hidden state, tiny and fast models) and benchmark honestly |

## 13. Open questions

- Is the goal a challenge submission, a research project, or a blog and simulation demo? The answer changes the whole roadmap.
- Can a ten-thousand-parameter rule carry enough chemistry, or does accuracy need a model large enough to erase the speed advantage?
- What exactly should the internal state represent, and what auxiliary data anchors it?
- How should one update step map to physical time, and can a model use adaptive steps near transition states?
- How is element identity encoded in the existing multi-species demo, and does that encoding scale past a handful of species?

## Sources

- Neural Particle Automata: Learning Self-Organizing Particle Dynamics (arXiv 2601.16096) and its project page, https://selforg-npa.github.io/
- Discovered Materials, Breaking the Speed–Accuracy Barrier in Quantum Chemistry, https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/
- Skala: Accurate and scalable exchange-correlation with deep learning (arXiv 2506.14665)
- Transition1x: a dataset for building generalizable reactive machine learning potentials (Scientific Data, 2022)
- Meta FAIR, Open Molecules 2025 (OMol25) and Universal Model for Atoms (UMA), https://ai.meta.com/blog/meta-fair-science-new-open-source-releases/
