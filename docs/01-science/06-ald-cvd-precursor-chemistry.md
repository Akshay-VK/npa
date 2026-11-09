---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: [02-density-functional-theory.md, 04-reaction-kinetics-and-rare-events.md]
---

# ALD/CVD precursor chemistry

The challenge's hidden benchmark is not general chemistry. It is specifically
"representative of atomic layer deposition (ALD) and chemical vapour deposition
(CVD) precursor chemistry". That phrase constrains which molecules matter, which
bonds break, and therefore which errors are fatal. This document explains the
process, the molecules, and the mismatch with the datasets the project intends
to use.

**Bottom line**

- ALD is a cyclic, self-limiting surface process; CVD is a continuous
  thermal/plasma process. Both build thin films from volatile metal-organic or
  metal-halide precursors.
- The chemistry is **metal–ligand chemistry**: M–C, M–N, M–Cl, M–O bonds, ligand
  elimination, and surface hydroxyl reactions.
- The project's initial scope (H/C/N/O, gas phase, no metals) does not overlap
  with this. That is the largest scope risk in the project
  ([R-07](../08-risk/01-risk-register.md)).
- GMTKN55 contains almost no organometallic chemistry; its closest subset is
  Al₂X₆ dimerisation. Doing well on GMTKN55 is not evidence of ALD competence.
- *(inference)* The hidden benchmark is most likely gas-phase thermochemistry
  and barriers for isolated precursor molecules and small fragments, because
  that is what a functional can be scored on. Surface reactions would require
  periodic boundary conditions and are much harder to standardise.

## What ALD is

Atomic layer deposition grows a film one atomic layer at a time by alternating
two self-limiting surface reactions.

A typical Al₂O₃ cycle using trimethylaluminium (TMA) and water:

1. **Precursor pulse.** TMA, Al(CH₃)₃, is dosed onto a hydroxylated surface.
   It reacts with surface –OH groups:
   $$\mathrm{Al(CH_3)_3(g) + 3\,{-}OH(s) \to Al({-}O)_3(s) + 3\,CH_4(g)}$$
   The reaction stops when all surface –OH sites are consumed. That is the
   *self-limiting* property: excess precursor does not keep depositing.
2. **Purge.** Unreacted TMA and methane are removed.
3. **Co-reactant pulse.** Water re-hydroxylates the surface:
   $$\mathrm{Al({-}O)_3(s) + 3\,H_2O(g) \to Al({-}OH)_3(s)}$$
4. **Purge.**

Each cycle adds roughly 1 Å of Al₂O₃. The cycle repeats until the target
thickness is reached.

**Why it matters industrially.** ALD gives conformal coatings on high-aspect-ratio
structures, atomic-level thickness control, and low deposition temperature. It is
used for gate dielectrics, barriers, and memory capacitors in semiconductor
manufacturing.

> **In plain words.** You paint the surface with one chemical, wash off the
> excess, paint it with another, wash again. Each coat is exactly one molecule
> thick because the first chemical runs out of places to stick.

## The precursors

The molecules that matter, with the bonds that break:

| Precursor | Formula | Film | Key bonds | Notes |
|---|---|---|---|---|
| **TMA** | Al(CH₃)₃ | Al₂O₃ | Al–C | Pyrophoric, dimerises as Al₂(CH₃)₆ |
| **TiCl₄** | TiCl₄ | TiO₂ | Ti–Cl | Corrosive byproduct HCl |
| **TEMAH** | Hf[N(CH₃)(C₂H₅)]₄ | HfO₂ | Hf–N | Bulky ligands, steric hindrance |
| **BTBAS** | SiH₂[N(H)(t-Bu)]₂ | SiO₂ | Si–N | Carbon-free Si precursor |
| **DIPAS** | SiH₂[N(i-Pr)₂]₂ | SiO₂ | Si–N | Alternative Si precursor |
| **Cu(dmap)₂** | Cu[N(CH₃)₂(CH₂CH₂NMe₂)]₂ | Cu | Cu–N | Copper interconnects |
| **Tris(dimethylamino)silane** | SiH[N(CH₃)₂]₃ | SiO₂ | Si–N, Si–H | Common aminosilane |

Structural features that make these hard for ML:

- **Metals.** Al, Ti, Hf, Cu. Different d-shell occupations, multiple oxidation
  states, and near-degenerate spin states.
- **Large, flexible ligands.** Ethyl and tert-butyl groups have many
  conformers, and the conformer energy differences are small.
- **Low-lying electronic states.** Metal amides and alkyls can be open-shell or
  have low-lying excited states, which single-reference DFT handles poorly.
- **Aggregation.** TMA is a dimer in the gas phase and in solution; the
  monomer–dimer equilibrium matters.
- **Reactive intermediates.** Ligand loss produces unsaturated fragments that
  may be transition-metal carbenes, radicals, or ions.

> **In plain words.** These are not simple organic molecules. They are metals
> wrapped in floppy carbon-and-nitrogen coats, and the interesting chemistry is
> the coat falling off.

## Why the datasets do not cover this

| Dataset | Elements | Chemistry | ALD relevance |
|---|---|---|---|
| Transition1x | H, C, N, O | Organic reactions | **None directly** — no metals |
| OMol25 | 83 elements, incl. metals | Molecules, metal complexes | **Partial** — contains metal complexes, but not precursor chemistry specifically |
| QM9 | H, C, N, O, F | Small organics | None |
| SPICE | H, C, N, O, S, P, halogens | Drug-like | None |
| GMTKN55 | Mostly main group | Thermochemistry | **Minimal** — closest is Al₂X₆ |
| OMat24 | Many, incl. metals | Inorganic solids | Materials, not molecules |

*(inference)* OMol25 is the only public dataset with meaningful metal–ligand
coverage, and even it is not targeted at ALD precursors. A model trained on
Transition1x has literally never seen a metal atom.

This is the core of
[the challenge-fit problem](../06-leaderboard/02-challenge-fit-analysis.md).
It is also why the project's charter explicitly excludes metals until phase 5.

> **In plain words.** Our training data is organic chemistry. The competition
> is metal chemistry. Those are different subjects, not different chapters.

## What the elementary steps look like

For a functional or a potential to be useful here, it must get these right:

1. **Ligand dissociation.** M–C or M–N bond breaking. Requires correct bond
   dissociation energies and correct spin state of the fragments.
2. **Surface reaction.** Precursor + surface hydroxyl → M–O bond + alkane.
   Requires a transition state and a barrier.
3. **Byproduct formation and desorption.** CH₄, HCl, or amine release.
4. **Adsorption and diffusion.** Physisorption energies, surface mobility.
5. **Nucleation.** Small cluster formation, which is where gas-phase
   thermochemistry and surface chemistry meet.

Steps 1, 2, and 5 are accessible to gas-phase cluster models and are the
plausible targets for a hidden benchmark scored by an XC functional. Steps 3
and 4 need a surface.

**Practical consequence.** A reaction surrogate evaluated on gas-phase
precursor fragmentation is a legitimate, testable proxy — but it is a proxy.
Any claim of ALD relevance must be stated as such.

> **In plain words.** Some of the important steps happen in the gas around the
> surface, and those you can test with ordinary molecules. The ones that happen
> on the surface need a surface model, which is a different project.

## The thermochemistry that matters

Quantities a benchmark would plausibly score, with rough magnitudes:

| Quantity | Typical range | Why it matters |
|---|---|---|
| M–C bond dissociation energy | 40–70 kcal/mol | Controls ligand loss |
| M–N bond dissociation energy | 50–90 kcal/mol | Controls amide precursor reactivity |
| M–Cl bond dissociation energy | 80–110 kcal/mol | TiCl₄ chemistry |
| Ligand elimination barrier | 20–50 kcal/mol | Sets deposition temperature |
| Precursor adsorption energy | 10–30 kcal/mol | Controls surface coverage |
| Dimerisation energy (e.g. Al₂Me₆) | 15–25 kcal/mol | Gas-phase speciation |
| Reaction energy (precursor + OH) | −20 to −60 kcal/mol | Driving force |

These are order-of-magnitude figures for orientation, not reference values.
Any number used in a benchmark must come from a cited calculation or
experiment.

*(inference)* The dimerisation energy of TMA is a good single test case: it is
small enough to compute accurately, involves two metal centres, and is
chemically central. It is also the kind of quantity that a functional can get
badly wrong while looking fine on organic thermochemistry.

> **In plain words.** The important numbers are how hard it is to pull a coat
> off a metal, how much energy that releases, and whether two precursors stick
> together. Those are exactly the numbers organic-chemistry benchmarks do not
> test.

## Test cases worth building

If the project ever extends to metals, these are the cheapest informative
systems:

1. **Al(CH₃)₃ monomer and dimer.** Tests metal–carbon bonds, dimerisation,
   and steric effects.
2. **Al(CH₃)₃ + H₂O → Al(OH)(CH₃)₂ + CH₄.** The core ALD half-reaction in a
   small cluster.
3. **TiCl₄ + H₂O.** Tests a different metal and halogen chemistry.
4. **Hf[N(CH₃)₂]₄ fragment.** Tests a heavier metal and M–N bonds.
5. **SiH₃OH and related silicon species.** Tests the silicon half of the
   process without a metal.

Each is small enough for CCSD(T) (up to ~10 heavy atoms) and large enough to
contain the relevant chemistry. That combination is rare and valuable.

*(inference)* A benchmark built from these five systems would be more relevant
to ALD than all of GMTKN55, and it could be computed at high accuracy by a
small team. That might be a better contribution than another model.

> **In plain words.** Five small molecules would test almost everything the
> competition cares about. Building that test might be more useful than trying
> to pass the existing one.

## What this means for the project

1. **State the gap explicitly.** Any public write-up must say the target
   chemistry is organic and the benchmark's chemistry is metal-organic.
2. **Do not claim ALD relevance** without at least one metal-containing test.
3. **Keep the five test cases as a stretch goal.** They are the natural bridge
   between the research result and the challenge.
4. **Expect the barrier error to be larger for metals.** If the model is
   already marginal on organic barriers, it will be worse here. Do not promise
   metals before organics work.

> **In plain words.** Be honest that we are not doing the competition's
> chemistry yet. The five small metal molecules are the stepping stones if we
> ever want to.

## Open questions

- Is the hidden benchmark gas-phase only, or does it include periodic surface
  models? This determines whether a gas-phase surrogate can ever be relevant.
- Which specific precursors does the benchmark use? The page does not say.
- Is there a public dataset of ALD precursor thermochemistry at CCSD(T)
  quality? A targeted search did not find one; this needs a proper literature
  review before assuming it does not exist.

## What would change this document

- A published description of the hidden benchmark's composition.
- Release of an ALD-precursor dataset at high accuracy.
- A decision by the project to include metals in phase 4, which would promote
  this document from context to specification.

## Sources

1. Discovered Materials, *Breaking the Speed–Accuracy Barrier in Quantum
   Chemistry* (benchmark description).
   <https://grandchallenges.discoveredmaterials.com/speed-accuracy-barrier/>
   (retrieved 2026-11-07).
2. George, *Atomic layer deposition: an overview*, Chem. Rev. 110, 111 (2010).
   <https://doi.org/10.1021/cr900056b> (retrieved 2026-11-07).
3. Johnson, Hultqvist and Bent, *A brief review of atomic layer deposition:
   from fundamentals to applications*, Mater. Today 17, 236 (2014).
   <https://doi.org/10.1016/j.mattod.2014.04.026> (retrieved 2026-11-07).
4. Levine et al., *OMol25*, arXiv:2505.08762 (element and chemistry coverage).
   <https://arxiv.org/abs/2505.08762> (retrieved 2026-11-07).
5. Goerigk et al., *GMTKN55*, Phys. Chem. Chem. Phys. 19, 32184 (2017)
   (subset composition).
   <https://doi.org/10.1039/C7CP04913G> (retrieved 2026-11-07).

> **Verification note.** The bond-energy ranges in the table are orientation
> figures drawn from general organometallic chemistry, not from a single cited
> compilation. Before any of them is used as a reference value, it must be
> replaced with a computed or experimental number and logged in
> [the verification log](../09-sources/02-verification-log.md).
