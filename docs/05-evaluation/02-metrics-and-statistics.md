---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: [01-evaluation-design.md, 02-verification-log.md]
---

# Metrics and statistics

MAE, RMSE, barrier error, WTMAD-2, rollout metrics, drift, and how to report
uncertainty with small samples. This is the canonical reporting template every
result must fill. No more, no less.

**Bottom line**

- The primary metric is chosen from the observable hierarchy (energy, barrier,
  rate). Everything else is secondary.
- WTMAD-2 is the challenge's metric, but the project may use a different primary
  metric. If so, WTMAD-2 must be reported alongside it.
- Uncertainty is reported via confidence intervals across seeds, not a single
  number. Three seeds and a mean are not evidence.
- Effect size must be declared before the experiment, and the number of seeds
  computed by a power analysis.

## The primary metric

Every experiment has one primary metric, chosen from the observable hierarchy:

| Tier | Metric | Formula | When to use |
|---|---|---|---|
| **1. Energy** | Mean Absolute Error (MAE) | $\frac{1}{N}\sum_i |E_i - E_i^\text{ref}|$ | Default; every model must report this. |
| **2. Barrier** | Barrier MAE | $\frac{1}{M}\sum_j |\Delta E^\ddagger_j - \Delta E^\ddagger_j^\text{ref}|$ | When the project's goal is barrier prediction. |
| **3. Rate** | Log-rate error | $\left|\log k - \log k^\text{ref}\right|$ | When the project's goal is rate prediction. |

> **In plain words.** Pick one number that the whole paper revolves around.
> The other metrics are secondary and reported in the table, but only one is
> the "primary" that the discussion centers on.

## The baseline set, always

Every result table must include these four reference values, in the order:

1. **PBE** WTMAD-2 / barrier MAE / time
2. **ωB97M-V** WTMAD-2 / barrier MAE / time
3. **Skala-1.1** WTMAD-2 / barrier MAE / time
4. **B3LYP-D3(BJ)** WTMAD-2 / barrier MAE / time

> **In plain words.** Four numbers. If you beat PBE on accuracy and cost, you
> have a point. If you beat ωB97M-V, you have a stronger point. If you beat
> Skala, you have a claim. More than that and you are overfitting.

## Uncertainty with small samples

Three seeds and a mean are not evidence. The contract requires reporting a
confidence interval or a seed-by-value table.

### Confidence interval (normal approximation)

If $s$ is the standard deviation of the metric across $n$ seeds:

$$
\text{CI} = \bar{x} \pm t_{0.975, n-1} \cdot \frac{s}{\sqrt{n}} .
$$

For $n = 5$, $t_{0.975, 4} \approx 2.78$. For $n = 3$, $t_{0.975, 2} \approx 4.30$.

**Important.** If the metric is not approximately normal (e.g. rate constants
are log-normally distributed), use the percentile interval or report the seed-by-value table.

### Percentile interval

Sort the $n$ seed values. The 95% interval is from the $\lceil 0.025 \cdot n \rceil$th
value to the $\lfloor 0.975 \cdot n \rfloor$th value.

For $n = 3$, the interval is the minimum to the maximum — which is honest but
uninformative. This is why the project targets $n \ge 5$.

### Seed-by-value table

When $n \le 3$, report the raw values and let the reader decide. Do not
compute a mean and an interval that you know is too narrow.

> **In plain words.** If you have 3 seeds and one gives 3.8, one gives 4.2,
> and one gives 5.1, the mean is 4.37 with a huge interval. Report the three
> numbers. Do not pretend the interval is small.

## Rollout stability metrics

For dynamics experiments, these metrics are reported alongside the primary
metric:

| Metric | Definition | Target |
|---|---|---|
| **Energy drift** | $|\Delta E| / \langle K \rangle$ over the trajectory | < 0.1% (NVE) |
| **RMSD growth** | $\sqrt{\frac{1}{N}\sum_i |\mathbf{x}_i(t) - \mathbf{x}_i(0)|^2}$ | Should plateau for conservative models |
| **Temperature drift** | $|T(t) - T(0)|$ (for NVT) | Small; depends on thermostat |
| **Max force** | $\max_t \|\mathbf{F}(t)\|$ | Should be bounded; spikes indicate instability |
| **Timestep sensitivity** | Metric value at $h$ and $2h$ | Ratio close to 1 indicates good scaling |

> **In plain words.** These are the seven checks from the rollout stability
> battery. If any of them fails, the model cannot be used for dynamics,
> regardless of single-point accuracy.

## Reporting template

Every result must fill this table, or an equivalent that covers the same fields:

| Field | Required content |
|---|---|
| **Primary metric** | Value + CI or seed table + protocol (basis, dispersion, etc.) |
| **Secondary metrics** | The other two tiers' values + CIs |
| **Baseline set** | PBE, ωB97M-V, Skala-1.1, B3LYP-D3(BJ) values + protocols |
| **Data split** | Train / test / validation sizes, provenance, checksum |
| **Model** | Architecture, parameter count, framework, random seed |
| **Training** | Loss type, learning rate, number of epochs, early stopping |
| **Evaluation** | Timestep, thermostat, ensemble, hardware, software versions |
| **Stability** | Energy drift, RMSD growth, max force (for dynamics) |
| **Open questions** | Any uncertainty or caveat the reader should note |

> **In plain words.** This table is the contract. If the result does not fill
> every row, it is incomplete. The reader uses this table to judge the claim.

## Effect size and power analysis

Before the experiment, the project must declare:

1. **The effect size** they are powered to detect. Example: "we are powered to
   detect a 0.5 kcal/mol difference in barrier MAE between two models at $p <
   0.05$ with 80% power."
2. **The number of seeds** needed. For a two-sample t-test, the formula is
   $n = 2 \cdot (z_{1-\alpha/2} + z_{1-\beta})^2 \cdot \sigma^2 / \delta^2$, where
   $\sigma$ is the estimated standard deviation and $\delta$ is the effect size.
3. **The actual number of seeds** run. If fewer than planned, report why and
   interpret the result cautiously.

> **In plain words.** You must decide what difference would matter before you
> start running. If you do not, you will always find "a difference" that is
> too small to care about.

## What would change this document

- A published evaluation protocol from the challenge organisers, which would
  standardise the metric protocol across projects.
- Evidence that a different metric (e.g. free-energy error) is more informative
  than the three-tier hierarchy, which would require a document rewrite.
- A new observable that the project decides to adopt, which would require
  adding a row to the reporting template.

## Open questions

- Is the normal approximation for the CI adequate, or should the percentile
  interval always be used for small $n$?
- How should the project handle the case where the primary metric is
  discontinuous (e.g. a model either crosses a barrier or it does not, across
  seeds)? This is the "binary success" problem.
- Should the baseline set always include Skala-1.1, even if the project is
  not comparing against learned functionals? It is the state-of-the-art
  learned functional, and its inclusion is a courtesy to the field.

## What would change this document

- A published evaluation protocol from the challenge organisers, which would
  standardise the metric protocol across projects.
- Evidence that a different metric (e.g. free-energy error) is more informative
  than the three-tier hierarchy, which would require a document rewrite.
- A new observable that the project decides to adopt, which would require
  adding a row to the reporting template.

## Sources

1. Goerigk et al., *A look at the density functional theory zoo with the
   advanced GMTKN55 database*, Phys. Chem. Chem. Phys. 19, 32184 (2017).
   <https://doi.org/10.1039/C7CP04913G> (retrieved 2026-11-07).
2. Bryenton and Johnson, *WTMAD-4: A Fair Weighting Scheme for GMTKN55*,
   arXiv:2509.23498. <https://arxiv.org/abs/2509.23498> (retrieved 2026-11-07).
3. Eyring, *The activated complex in chemical reactions*, J. Chem. Phys. 3,
   107 (1935). <https://doi.org/10.1063/1.1749604> (retrieved 2026-11-07).
4.Laio and Parrinello, *Escaping free-energy minima*, PNAS 99, 12562 (2002).
   <https://doi.org/10.1073/pnas.202427399> (retrieved 2026-11-07).
5. Bussi, Donadio and Parrinello, *Canonical sampling through velocity
   rescaling*, J. Chem. Phys. 126, 014101 (2007).
   <https doi.10.1063/1.2408420> (retrieved 2026-11-07).
6. Rothman et al., *A survey of power analysis methods*, BMC Medical Research
   Methodology 21, 13 (2021). <https://doi.org/10.1186/s12874-020-00151-x> (retrieved 2026-11-07).
7. Gelman et al., *Bayesian Data Analysis*, 4th ed., Chapman & Hall/CRC (2020).