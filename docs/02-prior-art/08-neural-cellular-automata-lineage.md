---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-landscape-and-taxonomy.md]
---

# Neural cellular automata lineage

NPA did not appear from nowhere. It sits at the end of a five-year line of
work that begins with a 2020 Distill article about growing lizard shapes on a
grid. Understanding that lineage matters because the project is proposing to
transplant the *end* of the line into a field where the *beginning* of the line
was already tried and abandoned. Knowing what each generation actually
contributed — and what each gave up — tells you what will and will not survive
the transplant.

**Bottom line**

- NCA's contribution is not the neural network; it is the *shared local rule*
  plus *iterated application*. That is genuinely valuable for chemistry.
- NCA's robustness and regeneration come from its training objective (reach a
  target state), not from the architecture. This is why they do not transfer.
- NPA's real technical contribution is differentiable SPH perception with
  analytic backward passes and CUDA kernels — an engineering result more than a
  scientific one.
- NPA explicitly does **not** enforce rotational equivariance. The paper says so
  in its limitations. This is a blocking issue for chemistry, not a detail.
- The "multi-species" demo is independent models composed, not a species
  mechanism. There is no element-conditioning machinery to borrow.

## Generation 1 — Neural cellular automata (2020)

Mordvintsev, Randazzo, Niklasson and Levin's *Growing Neural Cellular
Automata* (Distill, 2020) is the founding document. The setup:

- A grid of cells, each holding a state vector $\mathbf{S}_i \in \mathbb{R}^C$
  (typically 12–16 channels: RGBA, hidden channels, and an "alive" channel).
- **Perception:** fixed Sobel filters in $x$ and $y$ plus a Laplacian, applied
  to every channel. This gives each cell a local view of its neighbours.
- **Update:** a small MLP maps the perception vector to a state increment,
  applied only to a random subset of cells ($p = 0.5$).
- **Alive masking:** cells with near-zero alpha stop updating, which prevents
  the "dead" background from participating.
- **Training:** sample a random number of steps, backpropagate through the
  unrolled rollout, keep a pool of states to avoid catastrophic forgetting, and
  add an overflow regulariser to keep states bounded.

The result is a system that grows a target image from a single seed and
regenerates after damage.

**What is genuinely new here.** Not the neural network — small MLPs were
unremarkable. The new thing is the *claim that a single shared local rule,
applied repeatedly, can produce a specified global structure*. That is a
statement about the sufficiency of locality, and it is the same statement
chemistry makes: intermolecular forces are local, and global structure emerges.

**What is easy to miss.** The loss is on the rendered image at the final step,
not on the trajectory. Any path to the target is acceptable. This is the
attractor problem in embryo, and it is the reason the lineage does not transfer
cleanly. See [the critical assessment](../00-orientation/03-critical-assessment-of-the-idea-note.md).

> **In plain words.** The 2020 result was: give every cell the same tiny set of
> instructions, let them look only at their neighbours, run the instructions
> over and over, and a whole shape appears. That was surprising and beautiful.
> But the cells were only ever rewarded for ending up in the right shape, never
> for taking the right path.

## Generation 2 — NCA beyond the image grid (2021–2025)

The perception operator was progressively separated from the update rule. This
is the most important structural idea in the lineage.

| Work | Domain | What replaced convolution |
|---|---|---|
| Niklasson et al. 2021 | texture synthesis | same grid, better losses |
| Pajouheshgar et al. 2022–2024 | meshes, graphs | graph/mesh neighbourhood operators |
| Pajouheshgar et al. 2024b | PDE interpretation | showed NCA updates are discretised PDEs |
| Growing NCA 2025 | 2D/3D growth | hierarchical, multi-scale perception |
| Kim & Park 2025 | manifolds | differential operators on surfaces |

The lesson: **the update rule is portable; the perception operator is the
domain-specific part**. That is exactly the modularity the NPA-for-chemistry
idea depends on. If SPH perception is a reasonable stand-in for "what an atom
sees", the rest of the architecture can be reused.

> **In plain words.** Over five years, people kept the "same instructions for
> everyone, run repeatedly" idea and swapped out how cells see their
> neighbours: grid, mesh, graph, curved surface. The instructions did not need
> to change. That is encouraging for chemistry, where the neighbourhood is
> atoms rather than pixels.

## Generation 3 — Hand-designed particle self-organisation (2016–2022)

Running in parallel, a different community built particle systems that
self-organise without any learning:

- **Clusters** (Ventrella, 2016): particles with simple attraction/repulsion
  rules form emergent structures.
- **Particle Life** (Mohr, 2022): a matrix of pairwise attraction strengths
  produces surprisingly rich "ecosystems".
- **Particle Lenia** (Mordvintsev et al., 2022): continuous cellular automata
  lifted to particles, with a ring-shaped growth function.

These systems are beautiful and cheap. They are also **not learnable**: the
rules are designed by hand and tuned by eye. The NPA paper's related-work
section positions itself precisely against this: these systems have "dynamics
[that] are hand-designed and not trained from data".

The value of these systems to this project is as *intuition pumps*. They show
that a small set of pairwise rules can produce complex collective behaviour,
which is the physical intuition behind the whole idea. They do not show that
such rules can be *fitted to chemistry*.

> **In plain words.** Before anyone trained particle rules, people hand-tuned
> them and got lovely swarms and blobs. That proves the *format* can produce
> complexity. It does not prove the format can be fitted to real molecules.

## Generation 4 — NPA (2026)

Kim, Pajouheshgar, Süsstrunk, Jakob and Park, *Neural Particle Automata:
Learning Self-Organizing Particle Dynamics*, SIGGRAPH 2026,
[arXiv:2601.16096](https://arxiv.org/abs/2601.16096). This is the paper the
project is built on, so it is worth being precise about what it does.

### Perception: SPH operators

Each particle $i$ at position $\mathbf{x}_i$ with mass $m_i$ and state
$\mathbf{S}_i \in \mathbb{R}^C$ computes a perception vector from neighbours
within a support radius $\epsilon$:

$$
\mathbf{Z}_i = \big[\mathbf{S}_i,\ \tilde{\mathbf{S}}_i,\ \nabla\mathbf{S}_i,\ \nabla\rho_i\big],
$$

where the components are kernel-weighted sums:

| Operator | Formula | Output dim |
|---|---|---|
| Density | $\rho_i = \sum_j m_j W_\epsilon(\mathbf{r}_{ji})$ | 1 |
| Smoothing | $\tilde{\mathbf{S}}_i = \sum_j \frac{m_j}{\rho_j}\mathbf{S}_j W_\epsilon(\mathbf{r}_{ji})$ | $C$ |
| Density gradient | $\nabla\rho_i = \sum_j m_j W^\nabla_\epsilon(\mathbf{r}_{ji})$ | $D$ |
| Moment matrix | $\mathbf{M}_i = \sum_j \frac{m_j}{\rho_j}\mathbf{r}_{ji} W^\nabla_\epsilon(\mathbf{r}_{ji})^\top$ | $D\times D$ |
| Gradient (0th order) | $\nabla_0\mathbf{S}_i = \sum_j \frac{m_j}{\rho_j}(\mathbf{S}_j-\mathbf{S}_i)W^\nabla_\epsilon(\mathbf{r}_{ji})$ | $C\times D$ |
| Gradient (1st order) | $\nabla_1\mathbf{S}_i = \mathbf{M}_i^{-1}\nabla_0\mathbf{S}_i$ | $C\times D$ |

with $\mathbf{r}_{ji} = \mathbf{x}_j - \mathbf{x}_i$. The kernels are Poly6 for
smoothing and Spiky for gradients.

Three implementation choices matter more than they look:

1. **The moment-matrix correction is detached.** Differentiating through
   $\mathbf{M}_i^{-1}$ is unstable, so the paper uses
   $\nabla\mathbf{S}_i = \nabla_0\mathbf{S}_i + (\nabla_1\mathbf{S}_i - \nabla_0\mathbf{S}_i)\texttt{.detach()}$,
   falling back to $\nabla_0$ when $\det(\mathbf{M}_i) < 10^{-3}$. This is a
   gradient hack, not a derivation, and it means the model is not exactly
   optimising the function it appears to optimise.
2. **Vector features are log-scaled**,
   $\mathbf{v} \leftarrow \log(1+|\mathbf{v}|)\,\mathbf{v}/(|\mathbf{v}|+\eta)$,
   to stop large gradients destabilising training.
3. **Gradients are stopped with respect to positions** in the perception stage,
   which the authors report improves stability and allows larger learning rates.
   This is a significant physical compromise: the perception is not
   differentiated through geometry.

### Update rule

A two-layer MLP with ReLU, shared across particles:

$$
\Delta\mathbf{y}_i = \mathbf{W}_2\big(\mathbf{W}_1\mathbf{Z}_i + \mathbf{b}_1\big)_+,
\qquad
\mathbf{S}_i \leftarrow \mathbf{S}_i + \delta\,\Delta\mathbf{S}_i,\quad
\mathbf{x}_i \leftarrow \mathbf{x}_i + \delta\,\Delta\mathbf{x}_i,
$$

with $\delta \sim \mathrm{Bernoulli}(0.5)$. This is forward Euler with a random
mask. There is no energy, no force, no symplectic structure.

### Scale and symmetry

- **Parameter count:** 11k for 2D morphogenesis and texture synthesis, 38k for
  3D, 21k + 7k for point-cloud classification. The "as few as ten thousand"
  claim is accurate.
- **Translation and permutation invariance:** yes, by construction.
- **Scale equivariance:** designed in, by normalising total mass to 1 and
  scaling displacements by $\epsilon$.
- **Rotational equivariance:** **no.** The paper states it "does not enforce
  rotational equivariance in this work" and suggests Vector Neurons as a
  possible fix. It also lists "NPA's gradient perceptions assume global
  Euclidean basis, limiting the model's generalization over rotations" as a
  limitation.

That last point is decisive for chemistry. Rotating a molecule must not change
its energy or its dynamics. A model without rotational equivariance will
either need augmentation (expensive, approximate) or an equivariant
reformulation (a different architecture). See
[symmetry and conservation](../03-method-design/03-symmetry-equivariance-and-conservation.md).

### Stated limitations

The paper is unusually candid:

1. **No merge or split.** Particle count is fixed. Regions needing more
   resolution cannot recruit particles; dense regions make SPH slower.
2. **Global Euclidean basis.** Poor rotational generalisation, as above.
3. **Hyperparameter sensitivity.** "The learning dynamics are sensitive to
   hyperparameters."

For chemistry, limitation 1 is severe: a chemical reaction changes the number
of *relevant* local environments, and a model that cannot adapt particle
density across a bond-breaking event is structurally limited. Limitation 3 is
an engineering tax that will consume weeks.

### The multi-species demo, precisely

The paper's Figure 14 composes "multiple independently trained NPA 'species'"
in one simulation. Each particle follows its own learned rule. When groups
interpenetrate, they enter each other's neighbourhoods and interact "despite
never being co-trained", with outcomes from "near-independence to cooperation
and disruption".

This is not element conditioning. It is two models sharing a coordinate space.
There is no shared representation, no guarantee that the A→B and B→A
interactions agree, and no mechanism for a new element to inherit anything from
an old one. It is, in effect, a demonstration of the failure mode that
[element conditioning](../03-method-design/04-element-conditioning.md) is
designed to avoid.

> **In plain words.** The paper's "multiple species" video is two separately
> trained models dropped into the same box. They bump into each other, and
> sometimes it looks like cooperation and sometimes like a fight. There is no
> shared brain and no way for a new element to learn from an old one. So we
> cannot copy it; we have to design that part ourselves.

## What transfers to chemistry, and what does not

| Element | Transfers? | Why |
|---|---|---|
| Shared local rule | **Yes** | Chemistry is local; one rule for all atoms is the right prior |
| Iterated application | **Yes** | Dynamics is iterated application of a force law |
| SPH perception | **Yes, with redesign** | Atoms are particles; but SPH smooths, and chemistry needs exact pair sums |
| Small MLP | **Yes** | Parameter efficiency is a genuine selling point |
| Stochastic update mask | **No** | Non-physical noise unless mapped to Langevin dynamics |
| Endpoint/attractor loss | **No** | Rewards convergence, punishes reaction |
| Regeneration as a feature | **No** | A self-healing model will not break bonds |
| Fixed particle count | **No** | Reactions change local density; also atoms are conserved, so count is fixed but *identity* is not |
| Global Euclidean basis | **No** | Violates rotational invariance |
| CUDA hash-grid kernels | **Yes** | Reusable engineering for neighbour search |
| Detached moment matrix | **Maybe** | Stability hack; acceptable if documented |

> **In plain words.** Take the "one small rule for everyone, applied over and
> over" idea, and take the fast neighbour-search code. Leave the self-healing,
> the random updates, and the flat-coordinate assumptions behind. They are
> features of the graphics problem, not of physics.

## Recommendation

Build on NPA's **perception and update machinery**, not its **training
philosophy**.

- Reuse: SPH operator set as a feature extractor, hash-grid neighbour search,
  small shared MLP, log-scaling of vector features.
- Replace: the endpoint loss with force/energy matching; the Bernoulli mask
  with a thermostat; the Euclidean gradient features with equivariant ones.
- Do not reuse: the regeneration framing, the multi-species composition, or the
  claim that robustness is desirable.

The one thing worth stealing outright is the *parameter budget*. An 11k-parameter
rule that does something real would be a genuinely interesting result. That is
the headline the project should chase.

> **In plain words.** Copy the machinery, not the philosophy. The machinery is
> good engineering. The philosophy was designed for pictures.

## Open questions

- Is the detached moment-matrix correction stable when the loss includes
  forces, which are far more sensitive to geometry than image losses?
- Can the fixed-particle-count limitation be relaxed with learned merge/split
  events, and is that necessary for chemistry or merely nice?
- Does SPH perception actually help at atomistic densities, where neighbours are
  sparse and irregular, compared to a plain radial-basis descriptor?

## What would change this document

- An equivariant NPA variant published, which would remove the largest
  transfer obstacle.
- Evidence that the detached gradient trick fails under force supervision,
  which would force a redesign of the perception backward pass.
- A demonstration that merge/split is essential for reaction modelling, which
  would make the fixed-count limitation a project-level blocker.

## Sources

1. Kim, Pajouheshgar, Süsstrunk, Jakob, Park, *Neural Particle Automata:
   Learning Self-Organizing Particle Dynamics*, SIGGRAPH 2026,
   arXiv:2601.16096v3. <https://arxiv.org/abs/2601.16096> (retrieved
   2026-11-07). Sections 3.1–3.2, 4.4, and the Limitations paragraph.
2. Pajouheshgar et al., NPA project page. <https://selforg-npa.github.io/>
   (retrieved 2026-11-07).
3. Mordvintsev, Randazzo, Niklasson, Levin, *Growing Neural Cellular Automata*,
   Distill, 2020. <https://distill.pub/2020/growing-ca/> (retrieved
   2026-11-07).
4. Mordvintsev et al., *Particle Lenia*, 2022.
   <https://google-research.github.io/self-organising-systems/particle-lenia/>
   (retrieved 2026-11-07).
