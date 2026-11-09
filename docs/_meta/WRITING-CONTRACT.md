# Writing contract for the NPA documentation set

Every document in `docs/` must follow this contract. It exists so that forty
documents written at different times by different authors still read as one
body of work, and so that a reader can tell the difference between a measured
fact and an inference.

## 1. Front matter

Every file starts with exactly this block, then a level-1 title:

```markdown
---
status: draft | reviewed | stable
confidence: high | medium | low
last_verified: YYYY-MM-DD
depends_on: [relative paths]
---

# Title
```

- `confidence` describes the document's overall evidentiary strength, not how
  confident the prose sounds.
- `last_verified` is the date you last checked the primary sources, not the
  date you wrote the file.
- `depends_on` lists documents a reader should have read first. Use relative
  paths. Empty list is fine.

## 2. Required opening

Directly after the title, before any section:

1. **One paragraph** stating what question the document answers and why it
   matters for the NPA project. No preamble, no "in this document we will".
2. **A "Bottom line" block**: three to six bullets, each a claim the reader can
   act on. These are the only sentences a busy reader is guaranteed to read.
   Write them last.

## 3. Section shape

- Use `##` for major sections, `###` for sub-sections. Do not skip levels.
- Every `##` section ends with a plain-language block:

```markdown
> **In plain words.** Imagine ... [3–6 sentences. No jargon. No equations.
> An analogy that a smart person outside chemistry would understand. Name the
> thing being explained, then explain it as if to a curious fifteen-year-old.]
```

This is mandatory for every `##` section. It is not a summary of the section;
it is a second, simpler explanation of the same idea. If the section is
already simple, the plain-words block should still add an analogy or a concrete
example rather than restate.

- Do not put a plain-words block inside a plain-words block. Do not put one
  after the "Sources" section.

## 4. Evidence rules

These are hard rules. A document that breaks them is not finished.

1. **Every number needs a source.** Either an inline link at the point of use,
   or a bracketed key resolving in the Sources section. No orphan numbers.
2. **Never invent a citation.** If you cannot open the paper or page, do not
   cite it. Cite the arXiv abstract page, the DOI landing page, the dataset
   README, or the software documentation — something you actually retrieved.
3. **Separate measurement from inference.** Inferences are marked
   `*(inference)*`. Unverified claims are marked `*(unverified)*` and must
   appear in the document's Open Questions or Verification Log entry.
4. **Prefer primary sources.** A paper's own abstract or results table beats a
   blog post about the paper. A dataset's README beats a review's description
   of the dataset. Vendor marketing is not a source for a performance number.
5. **Report protocol with every benchmark number.** Basis set, reference level,
   system size, hardware, and whether dispersion correction was applied all
   change the number. A number without its protocol is decoration.
6. **Quote errors as the source states them.** If a paper says 2.8 kcal/mol on
   GMTKN55, write 2.8 and link it. Do not round to "about 3".
7. **Flag the date.** Fast-moving areas (universal potentials, learned
   functionals) change monthly. State the retrieval date for anything that
   could be stale.

## 5. Cross-linking

- Link to another document with a relative path and a reason:
  `see [Symmetry and equivariance](../03-method-design/03-symmetry-equivariance.md) for why this matters`.
- Link to a specific section with an anchor where useful.
- Never duplicate a table or a derivation that already lives in another
  document. Link instead and add only what is new. Duplication is how
  documentation rots.

## 6. Depth calibration

- Aim for 1,200–2,500 words per substantive document. Go longer only when the
  material genuinely needs it (a derivation, a full dataset table).
- Do not pad. If a section has three true sentences, it gets three sentences.
  A short honest document beats a long one with filler.
- Assume the reader is technically strong but new to *this* field. Define a
  term the first time it appears, then use it freely. The glossary holds the
  canonical definition; do not re-define terms already in `GLOSSARY.md` at
  length — one clause is enough.
- Equations: use `$...$` and `$$...$$`. Define every symbol on first use.
  Do not include an equation you cannot explain in the plain-words block.

## 7. Tone

- Direct, specific, unhedged where the evidence is clear.
- No marketing language ("revolutionary", "game-changing", "cutting-edge").
- No false balance: if the evidence says an approach fails, say it fails and
  cite the failure.
- Critique ideas, not people. The source note is a colleague's thinking; treat
  it with respect and correct it precisely where it is wrong.
- British spelling throughout (organisation, behaviour, generalise), matching
  the source note.

## 8. Required closing sections

Every document ends with, in this order:

```markdown
## Open questions
- ...

## What would change this document
- ...

## Sources
1. Author, *Title*, venue, year. URL (retrieved YYYY-MM-DD).
```

## 9. Failure modes to avoid

- **The survey trap.** Listing twenty methods without saying which one you
  would use and why. Every survey section must end with a recommendation.
- **The hedge spiral.** "It could potentially possibly be argued that..." Say
  what you think and mark it as inference.
- **The number soup.** A table of benchmark results with no protocol notes and
  no interpretation. Every table gets a "what this means" paragraph.
- **The copy-paste.** Restating the source note. The source note is an input,
  not a template. Add information, correct errors, resolve ambiguity.
- **The missing plain words.** Automatic fail. Every `##` section.
