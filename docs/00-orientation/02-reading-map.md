---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: []
---

# Reading map

Forty documents is a library, not a briefing. This map tells you which six of
them to read for your particular job, and in what order, so that you never read
a document whose prerequisites you have not met.

**Bottom line**

- Everyone reads four documents: the charter, the critical assessment, the
  landscape, and the risk register. That is the minimum viable understanding.
- Builders read the method-design cluster in numeric order; it is a single
  argument split across six files.
- Scientists and reviewers skip the implementation documents and read the
  science and evaluation clusters.
- If you only have an hour, read
  [the critical assessment](03-critical-assessment-of-the-idea-note.md) and
  [the landscape](../02-prior-art/01-landscape-and-taxonomy.md).

## The dependency graph

```
                    01-project-charter
                            |
                03-critical-assessment
                            |
        +-------------------+-------------------+
        |                   |                   |
  01-science/*        02-prior-art/*      04-what-you-need
        |                   |                   |
        +---------+---------+                   |
                  |                             |
          03-method-design/* <------------------+
                  |
        +---------+---------+
        |                   |
    04-data/*          05-evaluation/*
        |                   |
        +---------+---------+
                  |
          06-leaderboard/*
                  |
      +-----------+-----------+
      |                       |
  07-delivery/*          08-risk/*
                  |
              09-sources/*
```

Nothing in this graph is a hard prerequisite in the software sense. It is an
*argument* order: each layer assumes the vocabulary of the one above it.

> **In plain words.** Read the "why" before the "how". If you start with the
> architecture documents you will understand the words and miss the point,
> because half of them are arguing with the other half.

## Path 1 — The builder (default)

You are going to write the code.

1. [Project charter](01-project-charter.md) — what counts as success.
2. [Critical assessment](03-critical-assessment-of-the-idea-note.md) — what is
   wrong with the obvious plan.
3. [Landscape and taxonomy](../02-prior-art/01-landscape-and-taxonomy.md) —
   what already exists.
4. [Electronic structure primer](../01-science/01-electronic-structure-primer.md)
   and [DFT](../01-science/02-density-functional-theory.md) — what the labels
   mean.
5. [Architecture space](../03-method-design/01-architecture-space.md) →
   [Prediction targets](../03-method-design/02-what-the-network-predicts.md) →
   [Symmetry](../03-method-design/03-symmetry-equivariance-and-conservation.md)
   → [Element conditioning](../03-method-design/04-element-conditioning.md) →
   [Latent state and time](../03-method-design/05-latent-state-and-time-mapping.md)
   → [Long range](../03-method-design/06-long-range-interactions-and-charge.md).
   Read these in order; they build one design.
6. [Experiment protocols](../07-delivery/02-experiment-protocols.md) — what to
   run first.
7. [Reproducibility](../07-delivery/03-reproducibility-and-infrastructure.md) —
   how not to lose the result.

Skip on first pass: ALD/CVD chemistry, wavefunction methods, the bibliography.

> **In plain words.** Builders should read the six design documents as one
> continuous argument, then start with the toy-world protocol. Everything else
> can wait until you hit it.

## Path 2 — The scientist or domain reviewer

You know quantum chemistry and want to know whether this is nonsense.

1. [Critical assessment](03-critical-assessment-of-the-idea-note.md) — start
   with the objections, not the pitch.
2. [Landscape](../02-prior-art/01-landscape-and-taxonomy.md) — placement.
3. [MLIPs](../02-prior-art/05-machine-learned-interatomic-potentials.md) and
   [universal potentials](../02-prior-art/06-universal-potentials-and-foundation-models.md)
   — the real competition.
4. [Learned functionals](../02-prior-art/03-learned-exchange-correlation-functionals.md)
   — the adjacent, better-funded competition.
5. [Prediction targets](../03-method-design/02-what-the-network-predicts.md) —
   the scientific core.
6. [Symmetry and conservation](../03-method-design/03-symmetry-equivariance-and-conservation.md)
   — where physics can be violated.
7. [Risk register](../08-risk/01-risk-register.md) and
   [failure modes](../08-risk/02-failure-modes-catalogue.md) — whether the
   authors know what can go wrong.
8. [Verification log](../09-sources/02-verification-log.md) — whether the
   numbers are real.

Skip: infrastructure, compute budget, reading map.

> **In plain words.** A domain expert should read this as a claim under attack,
> not as a tutorial. Start with what could be wrong, then decide whether the
> defence is adequate.

## Path 3 — The sceptical reader with one hour

1. [Critical assessment](03-critical-assessment-of-the-idea-note.md), sections
   "The missing objection" and "What is genuinely novel here".
2. [Landscape](../02-prior-art/01-landscape-and-taxonomy.md), the comparison
   table.
3. [Provisional leaderboard](../06-leaderboard/01-provisional-leaderboard.md).
4. [Risk register](../08-risk/01-risk-register.md), the top five rows.

If those four survive your scrutiny, the rest is detail.

> **In plain words.** One hour is enough to decide whether to take the project
> seriously. Read the four places where it could be self-deceiving.

## Path 4 — The reader who wants the science, not the project

1. [Electronic structure primer](../01-science/01-electronic-structure-primer.md)
2. [DFT](../01-science/02-density-functional-theory.md)
3. [Wavefunction methods and error bars](../01-science/03-wavefunction-methods-and-error-bars.md)
4. [Reaction kinetics and rare events](../01-science/04-reaction-kinetics-and-rare-events.md)
5. [Molecular dynamics](../01-science/05-molecular-dynamics-and-ensembles.md)
6. [Units and scales](../01-science/07-units-scales-and-orders-of-magnitude.md)

That sequence is a self-contained mini-course in computational reaction
chemistry, with no NPA content at all.

> **In plain words.** The science cluster stands alone. If you are here to
> learn the chemistry rather than to judge the project, read 01 through 07 and
> stop.

## Reading conventions

- Every section ends with a **In plain words** block. If you are skimming,
  read those; they are written to be sufficient on their own for a
  non-specialist.
- Numbers marked *(inference)* are the authors' reasoning, not a source's
  measurement. Numbers marked *(unverified)* could not be checked.
- `depends_on` in each file's front matter is machine-readable; the graph above
  is the human-readable version.
- Benchmarks are meaningless without protocol. Every table that reports one
  states basis set, reference level, hardware, and dispersion treatment, or says
  explicitly that the source did not.

> **In plain words.** Skim the plain-words blocks if you are in a hurry, trust
> the ones marked as sources more than the ones marked as inference, and never
> believe a benchmark number that does not say how it was measured.

## Open questions

- Should there be a single-page executive summary above all of this? Probably
  yes once the results exist; premature now.
- Which documents should be published externally, and which are internal
  scratch? The risk register and verification log are internal by default.

## What would change this document

- If the document count grows past roughly sixty, the map needs to become a
  generated index rather than a hand-maintained one.
- If a reader reports that a path led them into a document they could not
  understand, the graph is wrong and should be re-cut.

## Sources

This document synthesises the set; it makes no external claims. The reading
order reflects the dependency structure declared in each file's front matter
and in [`_meta/DOC-MAP.md`](../_meta/DOC-MAP.md).
