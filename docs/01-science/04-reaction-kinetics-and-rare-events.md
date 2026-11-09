---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [03-wavefunction-methods-and-error-bars.md]
---

# Reaction kinetics and rare events

A barrier height is not a rate. The gap between the two is where most claims
about "predicting chemistry" quietly fail, because the conversion is
exponential and because the events themselves are rare enough that ordinary
simulation never sees them. This document covers transition state theory, the
timescale problem, and the sampling methods that exist to solve it.

**Bottom line**

- The rate depends exponentially on the barrier. A 1 kcal/mol barrier error is a
  factor of ~5 in rate at 300 K, and ~2.7 at 500 K.
- The prefactor matters too, and it carries entropy, tunnelling, and recrossing.
  Transition state theory ignores all three; it is a starting point, not the
  answer.
- Chemical events span roughly twelve orders of magnitude in time
  (10⁻¹⁵ s vibration to 10⁻³ s reaction). No brute-force simulation covers
  that range.
- Enhanced sampling methods are how the field bridges the gap, and they are
  multiplicative with a faster potential: 1000× faster potential means 1000×
  more sampling.
- A model evaluated only on barrier heights has not been evaluated on rates.
  Recrossing and prefactor errors can change the answer by an order of
  magnitude even with a perfect barrier.

## Transition state theory in one page

Eyring and Polanyi, 1935; the modern statement is in any kinetics textbook.

For a reaction with a first-order rate constant,

$$
k = \kappa \frac{k_B T}{h} \exp\!\left(-\frac{\Delta G^\ddagger}{RT}\right),
$$

where:

- $k_B T / h$ is the attempt frequency. At 298 K it is
  $6.21 \times 10^{12}\ \mathrm{s^{-1}}$.
- $\Delta G^\ddagger$ is the **activation free energy** — not the electronic
  barrier.
- $\kappa$ is the transmission coefficient, which corrects for recrossing
  ($\kappa < 1$) and tunnelling ($\kappa > 1$).

The electronic barrier $\Delta E^\ddagger$ is only one contribution to
$\Delta G^\ddagger$:

$$
\Delta G^\ddagger = \Delta E^\ddagger + \Delta ZPE + \Delta H_{\text{thermal}} - T\Delta S^\ddagger .
$$

Zero-point energy and thermal corrections are typically 1–3 kcal/mol. The
entropy term can be larger and of either sign: a loose transition state has
positive $\Delta S^\ddagger$ and a *lower* barrier in free energy than the
electronic value suggests.

**Consequence for this project.** A model trained to reproduce electronic
energies has, by construction, not learned any of these corrections. It can
still be useful — the electronic barrier is usually the dominant term — but any
claim about rates must either include the corrections or state that it is
reporting electronic barriers only.

> **In plain words.** The height of the hill is not the speed of the traffic.
> To get the speed you also need the width of the road, how many lanes, and how
> wobbly the cars are. The hill height is the biggest factor, but not the only
> one.

## Why a small barrier error is a large rate error

The sensitivity is set by $RT$:

| Temperature | $RT$ (kcal/mol) | Rate factor per 1 kcal/mol error |
|---|---|---|
| 300 K | 0.596 | 5.4× |
| 500 K | 0.993 | 2.7× |
| 1000 K | 1.987 | 1.65× |

And the full table of barrier errors:

| Barrier error | Factor at 300 K | Factor at 500 K |
|---|---|---|
| 0.1 kcal/mol | 1.18× | 1.11× |
| 0.5 kcal/mol | 2.3× | 1.6× |
| 1.0 kcal/mol | 5.4× | 2.7× |
| 2.0 kcal/mol | 29× | 7.4× |
| 5.0 kcal/mol | 4500× | 150× |

This is why "chemical accuracy" is conventionally 1 kcal/mol: it is roughly
the point at which a rate prediction is within an order of magnitude. For
selectivity between two competing channels, even 1 kcal/mol is marginal,
because what matters is the *difference* of two barriers, and errors partially
cancel — or partially anti-cancel.

> **In plain words.** Being 1 unit wrong about the hill makes you 5 times wrong
> about the speed at room temperature. Being 2 units wrong makes you 29 times
> wrong. Small errors in energy are huge errors in time.

## The timescale problem

A molecular vibration has a period of ~10–30 fs. A typical reaction at 500 K
with a 25 kcal/mol barrier has a rate of roughly $10^{-5}\ \mathrm{s^{-1}}$ —
one event per day per molecule. The ratio is about $10^{18}$.

No simulation can bridge that by brute force. Even with a 1 fs timestep, one
millisecond of dynamics is $10^{12}$ steps. At $10^6$ steps per GPU-second,
that is 11 days per trajectory — for a single event, if it happens at all.

**Three ways out:**

1. **Make the potential faster.** This is the project's contribution. It
   multiplies the sampling budget but does not change the exponent.
2. **Change the sampling.** Bias, heat, or constrain the system to force events
   to happen, then correct the statistics.
3. **Learn the event.** Predict rates directly from structure, skipping dynamics
   entirely. A different research programme.

The project is a (1) with (2) attached. It is not a (3), and should not claim
to be.

> **In plain words.** Reactions are so rare that normal simulation almost never
> sees one. There are three escapes: run faster, cheat the sampling, or learn
> the answer directly. We are doing the first, with some of the second.

## Enhanced sampling, briefly

The methods a reaction model must eventually be compatible with:

| Method | Mechanism | Needs a collective variable? | Output |
|---|---|---|---|
| **Umbrella sampling** | Harmonic bias in windows along a coordinate; unbias with WHAM/MBAR | Yes | Free-energy profile |
| **Metadynamics** | History-dependent Gaussian bias fills basins | Yes | Free energy, with reweighting |
| **Well-tempered metadynamics** | Bias grows more slowly, converges to a distribution | Yes | Free energy |
| **Replica exchange** | Parallel simulations at different temperatures, swap configurations | No | Thermodynamics |
| **Transition path sampling** | Shoot trajectories from the dividing surface | No | Mechanism, rate |
| **Hyperdynamics** | Add a bias that raises the basin floor without changing the mechanism | No | Accelerated rate |
| **Temperature acceleration** | Run hot, extrapolate with Arrhenius | No | Approximate rate |

Two practical points:

- **These methods require an energy function, not a position-update rule.** A
  direct-update NPA cannot be used with them, because biasing requires a
  potential. This is a strong argument for the energy-based variant
  independent of accuracy.
- **They are sensitive to model smoothness.** Biasing forces require continuous
  derivatives; a model with discontinuous forces will fail to converge.

*(inference)* The combination of a fast surrogate and well-tempered
metadynamics is the most convincing possible demonstration of this project's
value: a free-energy profile that matches DFT at a fraction of the cost. It
should be planned for phase 4, not treated as an afterthought.

> **In plain words.** These tricks push the molecule over the hill so you can
> watch what happens on the other side, then undo the push mathematically. They
> only work if the model has an energy you can push against.

## Recrossing and the transmission coefficient

Transition state theory assumes that every trajectory crossing the dividing
surface goes on to products. In reality, some cross and come back.

The transmission coefficient $\kappa$ is the fraction that commit. It is
usually between 0.1 and 1 in condensed phases, and can be much smaller when
friction is high (Kramers regime). In the gas phase for simple reactions it is
often close to 1.

Why it matters here: **a model can get the barrier exactly right and still get
the rate wrong by 10× if its dynamics recross more than the true system.** This
is a property of the *dynamics*, not the *energy surface*, and it is invisible
to any static benchmark. It is also the strongest argument for evaluating on
actual trajectories rather than only on energies.

> **In plain words.** Some molecules climb over the hill, change their mind,
> and slide back. If your model lets them do that more often than reality does,
> your reaction is too slow even though the hill is the right height.

## Tunnelling

Hydrogen transfer reactions can tunnel. At room temperature, tunnelling can
increase the rate by orders of magnitude for reactions involving H, and it is
larger at lower temperature. Transition state theory with a Wigner or
Eckart correction is the usual approximation.

For this project, tunnelling is a known omission, not a bug. A classical
trajectory model cannot reproduce it. It should be stated as a limitation in
any rate claim, and it is one reason why H + H₂ is a good phase-3 test (it is
also a case where accurate quantum dynamics exist for comparison).

> **In plain words.** Light atoms can cheat and pass through the hill instead
> of over it. Classical simulations cannot show that. Say so.

## What this means for evaluation

Five rules for any rate-related claim:

1. **Never report a rate from a barrier alone.** State whether the prefactor
   and ZPE corrections were included.
2. **Report the temperature.** A barrier error that is acceptable at 1000 K is
   not acceptable at 300 K.
3. **Compare on the same free-energy definition.** Electronic barrier,
   ZPE-corrected barrier, and activation free energy are three different
   numbers.
4. **Check recrossing** if you run trajectories. Report the transmission
   coefficient or at least the commitment probability.
5. **State the tunnelling treatment**, or state that there is none.

See [metrics and statistics](../05-evaluation/02-metrics-and-statistics.md) for
the reporting template.

> **In plain words.** Five sentences of caveat turn a barrier number into a
> rate claim. Without them, it is just a number.

## Open questions

- Is the project's target observable the electronic barrier, the free-energy
  barrier, or the rate? Each implies a different model and a different
  benchmark. This should be decided before phase 3.
- How large is the recrossing error for a learned potential that conserves
  energy but has slightly wrong curvature at the saddle?
- Can tunnelling be added post hoc with a standard correction, or does it
  require a quantum dynamics layer?

## What would change this document

- A demonstration that barrier error dominates all other error sources in the
  target chemistry, which would justify ignoring prefactors and recrossing.
- Evidence that the target ALD/CVD reactions are dominated by surface
  processes where the gas-phase TST picture is inadequate, which would change
  the whole evaluation design.

## Sources

1. Eyring, *The activated complex in chemical reactions*, J. Chem. Phys. 3, 107
   (1935). <https://doi.org/10.1063/1.1749604> (retrieved 2026-11-07).
2. Laidler and King, *Development of transition-state theory*, J. Phys. Chem.
   87, 2657 (1983). <https://doi.org/10.1021/j100238a002> (retrieved
   2026-11-07).
3. Kramers, *Brownian motion in a field of force and the diffusion model of
   chemical reactions*, Physica 7, 284 (1940).
   <https://doi.org/10.1016/S0031-8914(40)90098-3> (retrieved 2026-11-07).
4. Laio and Parrinello, *Escaping free-energy minima*, PNAS 99, 12562 (2002).
   <https://doi.org/10.1073/pnas.202427399> (retrieved 2026-11-07).
5. Barducci, Bussi and Parrinello, *Well-tempered metadynamics*, Phys. Rev.
   Lett. 100, 020603 (2008).
   <https://doi.org/10.1103/PhysRevLett.100.020603> (retrieved 2026-11-07).
6. Frenkel and Smit, *Understanding Molecular Simulation*, 2nd ed., Academic
   Press (2002). Textbook; no URL. Chapters 7 and 13.
