---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-landscape-and-taxonomy.md]
---

# Machine-learned interatomic potentials

Everything in this document already works, at scale, and is the baseline any
NPA-based model will be judged against. The purpose is not to survey the field
for its own sake but to extract the four design decisions that every successful
MLIP makes, so that the project can decide which ones to keep, which to break,
and what breaking them would cost.

**Bottom line**

- Every modern MLIP rests on one assumption: the total energy is a sum of
  local contributions, each depending only on atoms within a cutoff. This is
  what makes them fast, transferable, and *wrong at long range*.
- The field's progress has come from three levers: better descriptors (learned
  instead of hand-designed), higher body order, and equivariance.
- Message passing buys accuracy at the cost of locality and speed. Allegro and
  MACE show you can get most of the accuracy with strict locality.
- The failure mode that matters for this project is not accuracy on equilibrium
  data — it is confident nonsense on bond-breaking geometries.
- An NPA model that predicts energy can borrow all of this machinery. An NPA
  model that predicts positions directly cannot, and will be compared
  unfavourably on every axis except speed.

## The one assumption everything rests on

An MLIP writes

$$
E(\{\mathbf{x}_i, Z_i\}) = \sum_i E_i\big(\{\mathbf{x}_j, Z_j\}_{j \in \mathcal{N}(i)}\big),
$$

where $\mathcal{N}(i)$ is the set of atoms within a cutoff radius $r_c$ of atom
$i$. Forces follow by automatic differentiation:

$$
\mathbf{F}_a = -\frac{\partial E}{\partial \mathbf{x}_a}.
$$

Three properties come free from this construction:

- **Extensivity.** Doubling the system doubles the energy.
- **Permutation invariance.** Reordering atoms does not change anything.
- **Translational invariance.** Shifting all atoms does not change anything.
- **Force consistency.** Forces are the exact gradient of the energy, so
  Newton's third law and energy conservation hold.

And one property does not:

- **Long-range physics.** Electrostatics and dispersion decay as $1/r$ and
  $1/r^6$, not to zero at 5 Å. A finite cutoff truncates them, and the model
  learns to compensate *within* the cutoff, which works until it does not.

This is the central trade-off of the field, and it is why
[long-range interactions](../03-method-design/06-long-range-interactions-and-charge.md)
is a whole document rather than a footnote.

> **In plain words.** Every atom is assumed to care only about its immediate
> neighbours. That is why these models are fast and why they can be trained on
> small molecules and used on big ones. It is also why they get the weak
> long-distance forces wrong: those forces come from far away, and the model
> has been told to ignore far away.

## The four design decisions

### 1. How to describe a local environment

| Generation | Descriptor | Example |
|---|---|---|
| Hand-designed | Radial and angular symmetry functions | Behler–Parrinello (2007) |
| Learned, invariant | Continuous-filter convolutions on distances | SchNet (2017) |
| Learned, directional | Messages with angular information | DimeNet (2020) |
| Learned, equivariant | Scalar + vector (and higher tensor) features | PaiNN (2021), NequIP (2022) |
| Learned, high body order | 4-body messages without deep message passing | MACE (2022–2023) |

The trend is uniform: **push the physics into the architecture rather than the
features**. Symmetry functions encode chemistry by hand; equivariant tensor
features encode it by construction.

### 2. How far information travels

- **Message passing** (SchNet, DimeNet, NequIP, MACE): each layer lets atoms
  exchange information with neighbours, so after $L$ layers information has
  travelled $L \times r_c$. Effective receptive field grows with depth.
- **Strict locality** (Allegro, 2023): no message passing between layers; each
  atom's energy depends only on its own neighbourhood, with high body order
  replacing depth.

Strict locality wins on scalability and parallelisability. Message passing wins
on accuracy per parameter. The empirical finding, summarised in a 2025
user-perspective comparison, is that "MACE and Allegro offer the highest
accuracy" among the models tested, with NequIP ahead for some specific
chemistry such as Si–O
([Leimeroth et al., 2025](https://iopscience.iop.org/article/10.1088/1361-651X/adf56d/pdf)).

### 3. Whether to be equivariant

Equivariance means: rotate the input, and the output rotates with it. An
invariant energy and equivariant forces are the physically correct behaviour.

- Invariant models (SchNet, ANI) achieve it by using only invariant scalars
  (distances, angles).
- Equivariant models (NequIP, MACE, Allegro) carry vectors and tensors through
  the network, which preserves directional information and improves data
  efficiency.
- The cost is implementation complexity and per-atom inference time.

*(inference)* For this project the choice is not optional. A model that is not
rotationally equivariant will fail the most basic physical test — rotate a
molecule, get a different energy — and no amount of augmentation fully fixes it
at inference time.

### 4. What to predict

Most MLIPs predict a scalar energy and obtain forces by autodiff. Some predict
forces directly (faster, no conservation guarantee). A few predict both plus
auxiliary quantities. The choice determines whether the model can report
barriers at all. See
[prediction targets](../03-method-design/02-what-the-network-predicts.md).

> **In plain words.** Four choices define an MLIP: how you describe an atom's
> surroundings, how far away it is allowed to look, whether the model rotates
> properly, and whether it predicts energy or motion. Every architecture in the
> literature is a point in that four-dimensional space.

## The comparison that matters

I am deliberately not quoting force errors in meV/Å, because they are not
comparable across datasets and protocols, and because a low force MAE on
equilibrium MD17 says nothing about barrier heights. What matters is the shape
of the trade-off.

| Model | Locality | Equivariant | Body order | Relative cost | Data efficiency | Maturity |
|---|---|---|---|---|---|---|
| ANI-1x / ANI-1ccx | strict | no | 3-body (symmetry functions) | very low | low | mature |
| SchNet | message passing | no | 2-body | low | medium | mature |
| DimeNet | message passing | no (directional) | 3-body | medium | medium | dated |
| PaiNN | message passing | vector | 3-body | medium | high | good |
| NequIP | message passing | tensor | 3-body | high | very high | good |
| Allegro | strict | tensor | 3-body | high | very high | good |
| MACE | message passing (2 layers) | tensor | 4-body | high | very high | best-supported |
| UMA | message passing + MoE | tensor | high | very high | pretrained | new |

"Relative cost" is per-atom inference, order-of-magnitude only. The ranking is
robust; the ratios are not.

**The practical read.** If you want a strong baseline tomorrow with minimal
effort, use MACE or a pretrained UMA. If you want to understand the design
space, implement a small invariant model first, then add equivariance, then add
body order. Do not start with the most complex architecture.

> **In plain words.** The best current models all agree on the same four
> choices: learn the description, keep it local, build in rotation, and use
> high body order. The differences between them are smaller than the
> difference between any of them and a model that gets those four wrong.

## Where MLIPs fail, precisely

This is the part that matters for a reactive surrogate.

**1. Bond breaking is out of distribution.** Training data for almost all
MLIPs consists of near-equilibrium configurations from MD or relaxation.
Stretched bonds and transition states are rare or absent. The model
extrapolates smoothly into a region where the true PES has a saddle and a
different electronic state, and it gets it wrong without warning. Transition1x
exists precisely because of this: its authors show that "ML models cannot learn
features in transition-state regions solely by training on hitherto popular
benchmark datasets"
([arXiv:2207.12858](https://arxiv.org/abs/2207.12858)).

**2. Long-range electrostatics are truncated.** A cutoff of 5 Å captures the
first solvation shell and nothing beyond. Charge transfer, ionic pairing, and
dispersion between separated fragments are all wrong.

**3. Charge and spin are not represented.** Most MLIPs assume neutral, closed
shell, fixed charge. OMol25 explicitly includes "variable charge/spin"
([arXiv:2505.08762](https://arxiv.org/abs/2505.08762)), which is a significant
departure and an admission that the standard assumption is limiting.

**4. Locality is a lie for metals and conjugated systems.** Electronic
structure is delocalised; a local model has to fake it. The error is small for
saturated organics and large for transition metals.

**5. Extrapolation is silent.** A neural network does not know it is out of its
training distribution. It returns a number with the same confidence as an
interpolation. This is the most dangerous property of the entire family.

*(inference)* Point 5 is the reason the field is moving toward uncertainty
quantification and ensemble disagreement, and the reason a physically
constrained architecture (energy-based, equivariant, with explicit long-range
terms) is worth its complexity: it fails more gracefully.

> **In plain words.** These models are brilliant interpolation engines. Show
> them a molecule like the ones they trained on and they are nearly perfect.
> Show them a bond halfway broken and they will give you a confident,
> smooth-looking, completely wrong answer.

## What an NPA model must beat

Three concrete bars, in increasing difficulty:

1. **PBE at PBE cost.** If a small particle automaton cannot match a GGA
   functional on barrier heights while being comparably fast, the architecture
   has no claim.
2. **MACE or UMA on a narrow reaction set, at lower cost.** This is the real
   test. It requires an energy interface, because otherwise there is no barrier
   to compare.
3. **A pretrained universal potential fine-tuned on the target chemistry.**
   This is the strongest realistic baseline and the one a reviewer will
   propose. If fine-tuning UMA on Transition1x beats the NPA model, the NPA
   architecture has to justify itself on cost or interpretability instead.

Any of these can be run in days. All of them should be run before writing a
paper.

> **In plain words.** Three opponents, in order: the cheap classical method,
> the best open model, and the best open model after a week of fine-tuning.
> Beat all three or explain why not.

## What is worth borrowing

Almost everything, and this is a feature not an embarrassment:

- **Energy-and-autodiff-force architecture.** Non-negotiable if barriers matter.
- **Equivariant features.** Non-negotiable for physical correctness.
- **Cutoff plus explicit long-range correction.** Cheaper than learning
  long-range physics from local data.
- **Sum-of-local-energies decomposition.** Gives extensivity for free and
  matches the locality prior.
- **Uncertainty quantification.** At minimum, ensemble disagreement, so the
  model can say "I have not seen this".

The only thing the project should *not* borrow is the assumption that a local
environment is sufficient for reactions. That assumption is exactly what the
NPA hypothesis is testing against.

> **In plain words.** Steal the whole toolbox. The only idea we are testing is
> whether adding memory to the toolbox helps. Everything else is settled
> engineering.

## Open questions

- Does the persistent-state idea survive when the model must be equivariant?
  State channels are scalars, so they can be invariant; but state that carries
  direction needs care.
- How much of a small model's accuracy gap can be closed by better data rather
  than more parameters? This is the central cost question.
- Is strict locality (Allegro-style) compatible with SPH perception, which is
  already local? Intuitively yes, and it would make the model very fast.

## What would change this document

- A published MLIP with persistent cross-step state, which would remove the
  project's novelty claim.
- Evidence that message passing is unnecessary at atomistic densities, which
  would simplify the architecture considerably.
- A universal potential that closes the barrier-height gap, which would make
  the reactive-surrogate niche much smaller.

## Sources

1. Behler and Parrinello, *Generalized neural-network representation of
   high-dimensional potential-energy surfaces*, Phys. Rev. Lett. 98, 146401
   (2007). <https://doi.org/10.1103/PhysRevLett.98.146401> (retrieved
   2026-11-07).
2. Schütt et al., *SchNet — A deep learning architecture for molecules and
   materials*, J. Chem. Phys. 148, 241722 (2018).
   <https://doi.org/10.1063/1.5019779> (retrieved 2026-11-07).
3. Batzner et al., *E(3)-equivariant graph neural networks for data-efficient
   and accurate interatomic potentials* (NequIP), Nature Communications 13,
   2453 (2022). <https://doi.org/10.1038/s41467-022-29939-5> (retrieved
   2026-11-07).
4. Batatia et al., *MACE: Higher order equivariant message passing neural
   networks for fast and accurate force fields*, NeurIPS 2022.
   <https://arxiv.org/abs/2206.07697> (retrieved 2026-11-07).
5. Musaelian et al., *Learning local equivariant representations for
   large-scale atomistic dynamics* (Allegro), Nature Communications 14, 579
   (2023). <https://doi.org/10.1038/s41467-023-36329-y> (retrieved 2026-11-07).
6. Leimeroth et al., *Machine-learning interatomic potentials from a user's
   perspective: a comparison of accuracy, speed and data efficiency*, Modelling
   Simul. Mater. Sci. Eng. (2025).
   <https://iopscience.iop.org/article/10.1088/1361-651X/adf56d/pdf> (retrieved
   2026-11-07).
7. Schreiner et al., *Transition1x*, arXiv:2207.12858.
   <https://arxiv.org/abs/2207.12858> (retrieved 2026-11-07).
8. Levine et al., *OMol25*, arXiv:2505.08762.
   <https://arxiv.org/abs/2505.08762> (retrieved 2026-11-07).
