---
status: draft
confidence: high
last_verified: 2026-11-07
depends_on: []
---

# Units, scales, and orders of magnitude

The reference card. Every conversion factor and typical magnitude the project
needs, in one place, with the sanity checks that catch most unit errors. If a
number looks wrong, it is usually wrong by a factor of 27.2, 23.06, or 627.5.
Those three numbers account for the majority of mistakes in this field.

**Bottom line**

- Energy: **1 Hartree = 27.2114 eV = 627.51 kcal/mol**. Most confusion comes
  from mixing Hartree-based codes with eV-based ML pipelines.
- Length: **1 bohr = 0.529177 Å**. Most codes use bohr internally and Å in
  input files.
- Force: **1 Hartree/bohr = 51.4221 eV/Å**.
- Thermal energy at 300 K is **0.0259 eV = 0.596 kcal/mol**. Chemical accuracy
  (1 kcal/mol) is about 1.7 × thermal energy at room temperature.
- A typical bond vibration period is 10–30 fs, which is why MD timesteps are
  ~1 fs.

## Energy

| From | To | Multiply by |
|---|---|---|
| Hartree (Eₕ) | eV | 27.211386 |
| Hartree | kcal/mol | 627.5095 |
| Hartree | kJ/mol | 2625.500 |
| Hartree | cm⁻¹ | 219474.63 |
| eV | kcal/mol | 23.06055 |
| eV | kJ/mol | 96.48533 |
| eV | cm⁻¹ | 8065.544 |
| kcal/mol | kJ/mol | 4.184 |
| kcal/mol | eV | 0.0433641 |
| kcal/mol | cm⁻¹ | 349.755 |
| kJ/mol | kcal/mol | 0.239006 |
| cm⁻¹ | eV | 1.23984 × 10⁻⁴ |
| cm⁻¹ | kcal/mol | 2.85914 × 10⁻³ |

**The three numbers to memorise.** 27.2114 (Hartree↔eV), 627.51
(Hartree↔kcal/mol), 23.061 (eV↔kcal/mol). Note that 627.51 / 23.061 = 27.211,
so if two of them agree the third will.

> **In plain words.** There are three energy currencies and one exchange rate
> between each pair. Learn three numbers and you can convert anything.

## Length, force, mass, time

| Quantity | Conversion |
|---|---|
| bohr → Å | × 0.529177 |
| Å → bohr | × 1.889726 |
| eV/Å → N | × 1.602177 × 10⁻⁹ |
| Hartree/bohr → eV/Å | × 51.42207 |
| eV/Å → Hartree/bohr | × 0.0194469 |
| atomic mass unit (u) → kg | × 1.660539 × 10⁻²⁷ |
| u → electron masses | × 1822.889 |
| g/mol → kg per particle | × 1.660539 × 10⁻²⁷ |

**Force sanity check.** A typical chemical bond has a force constant of
~500 N/m. Stretching it by 0.1 Å gives a force of
$500 \times 10^{-11} = 5 \times 10^{-9}$ N ≈ 3 eV/Å. If a computed force is
1e-3 eV/Å or 1e3 eV/Å, something is wrong.

> **In plain words.** Forces should be a few eV per ångström for ordinary
> bonds. Orders of magnitude outside that range mean a unit error or a broken
> structure.

## Thermal and statistical

| Quantity | Value |
|---|---|
| $k_B$ | 8.617333 × 10⁻⁵ eV/K |
| $k_B$ | 3.166811 × 10⁻⁶ Hartree/K |
| $k_B$ | 1.987204 × 10⁻³ kcal/(mol·K) |
| $k_B T$ at 298.15 K | 0.025693 eV = 0.59248 kcal/mol |
| $k_B T$ at 300 K | 0.025852 eV = 0.59614 kcal/mol |
| $k_B T$ at 500 K | 0.043087 eV = 0.99357 kcal/mol |
| $k_B T$ at 1000 K | 0.086173 eV = 1.98714 kcal/mol |
| $RT$ at 298.15 K | 0.59248 kcal/mol = 2.47896 kJ/mol |
| $k_B T/h$ at 298 K | 6.21 × 10¹² s⁻¹ |

**Chemical accuracy.** 1 kcal/mol = 4.184 kJ/mol = 0.04336 eV = 43.36 meV =
349.8 cm⁻¹. This is the conventional target for thermochemistry, and it is
about 1.7 $k_B T$ at room temperature.

> **In plain words.** Room temperature gives every molecule about 0.6 kcal/mol
> of jiggle. "Chemical accuracy" is 1 kcal/mol, so it means being right to
> within about two jiggles. That is the standard the whole field uses.

## Typical magnitudes

Use these to sanity-check any computed number.

| Quantity | Typical value | Range |
|---|---|---|
| Covalent bond length | 1.0–1.6 Å | 0.74 (H₂) to 2.4 (I–I) |
| C–H bond | 1.09 Å | — |
| O–H bond | 0.96 Å | — |
| C–C single bond | 1.54 Å | — |
| Bond dissociation energy (single) | 80–100 kcal/mol | 35 (F–F) to 110 (C–O) |
| Reaction barrier | 5–40 kcal/mol | 0 to 100 |
| Reaction energy | −100 to +100 kcal/mol | — |
| Hydrogen bond | 1–10 kcal/mol | — |
| Dispersion (per pair, contact) | 0.1–2 kcal/mol | — |
| Conformer energy difference | 0.1–5 kcal/mol | — |
| Vibrational frequency | 500–4000 cm⁻¹ | — |
| Vibrational period | 8–70 fs | — |
| MD timestep | 0.5–2 fs | — |
| Thermal velocity (300 K, C) | ~600 m/s | — |
| Diffusion coefficient (liquid) | 10⁻⁹ m²/s | — |

> **In plain words.** A chemical bond is about one ångström long and costs
> about a hundred units to break. A reaction barrier is a fraction of that. If
> your model predicts a 500-unit barrier, it is wrong.

## Time scales

| Process | Time scale |
|---|---|
| Electronic motion | 10⁻¹⁷–10⁻¹⁵ s |
| Bond vibration | 10⁻¹⁴–10⁻¹³ s |
| Hydrogen bond lifetime | 10⁻¹²–10⁻¹¹ s |
| Conformational change | 10⁻¹¹–10⁻⁹ s |
| Solvent relaxation | 10⁻¹¹–10⁻¹⁰ s |
| Reaction with 20 kcal/mol barrier at 300 K | ~10⁰ s |
| Reaction with 30 kcal/mol barrier at 300 K | ~10⁵ s |
| Protein folding | 10⁻⁶–10⁰ s |
| ALD cycle | 10⁻¹–10¹ s |

**The gap.** A 1 fs timestep against a 1 s reaction is a factor of 10¹⁵. This
is why brute-force MD cannot see chemistry, and why enhanced sampling exists
(see [reaction kinetics](04-reaction-kinetics-and-rare-events.md)).

> **In plain words.** Electrons move in attoseconds, bonds vibrate in
> femtoseconds, molecules react in seconds. That is fifteen orders of
> magnitude, and no computer can step through all of it.

## Worked sanity checks

**Check 1 — is this barrier reasonable?**
A DFT calculation reports a barrier of 0.0063 Hartree. Multiply by 627.51:
3.95 kcal/mol. Plausible for a low barrier. If you had read it as eV, you would
get 0.0063 eV = 0.15 kcal/mol, which is not a barrier at all.

**Check 2 — is this force reasonable?**
An ML model reports a force of 0.35 eV/Å. Convert to Hartree/bohr:
0.35 × 0.01945 = 0.0068. Plausible. If the model had been trained in
Hartree/bohr and you read the output as eV/Å, you would get 0.0068 eV/Å, which
is 50× too small and would make the dynamics nearly frozen.

**Check 3 — is this rate reasonable?**
A 20 kcal/mol barrier at 300 K. $\exp(-20/0.596) = \exp(-33.6) = 2.5 \times
10^{-15}$. Multiply by $6.2 \times 10^{12}$ s⁻¹ gives $1.5 \times 10^{-2}$
s⁻¹, i.e. about one event per minute. For a 25 kcal/mol barrier the exponent
is −42, giving $10^{-5}$ s⁻¹, about one per day. Getting a rate of $10^{6}$
s⁻¹ from a 25 kcal/mol barrier means a unit or prefactor error.

**Check 4 — is this energy per atom reasonable?**
A model reports −4.2 eV/atom for an organic molecule. Carbon's cohesive energy
is ~7.4 eV/atom, and molecular binding is a fraction of that. −4.2 eV/atom is
plausible for a dense solid, suspicious for a molecule. Always check the
reference: total energies are large and negative, and only differences are
meaningful.

> **In plain words.** Four checks, each takes ten seconds. They will catch most
> of the errors that would otherwise become a week of debugging.

## Conventions by code

| Code | Energy unit | Length unit | Force unit |
|---|---|---|---|
| PySCF | Hartree | bohr | Hartree/bohr |
| ORCA | Hartree | Å (input), bohr (internal) | Hartree/bohr |
| Gaussian | Hartree | Å | Hartree/bohr |
| VASP | eV | Å | eV/Å |
| CP2K | Hartree | bohr | Hartree/bohr |
| ASE | eV | Å | eV/Å |
| LAMMPS | depends on `units` | depends | depends |
| MACE / NequIP | eV | Å | eV/Å |
| OMol25 / UMA | eV | Å | eV/Å |

*(inference)* The ML ecosystem has converged on eV and Å; the quantum chemistry
ecosystem has not. Every interface between them is a conversion site and should
be tested explicitly, not assumed.

> **In plain words.** Quantum chemistry programs speak Hartree and bohr. Machine
> learning programs speak eV and ångström. Every bridge between them is a place
> where a factor of 27 can go missing.

## Constants

| Constant | Value | Units |
|---|---|---|
| $h$ | 4.135667696 × 10⁻¹⁵ | eV·s |
| $\hbar$ | 6.582119569 × 10⁻¹⁶ | eV·s |
| $c$ | 2.99792458 × 10⁸ | m/s |
| $N_A$ | 6.02214076 × 10²³ | mol⁻¹ |
| $e$ | 1.602176634 × 10⁻¹⁹ | C |
| $m_e$ | 9.1093837015 × 10⁻³¹ | kg |
| $a_0$ | 5.29177210903 × 10⁻¹¹ | m |
| $E_h$ | 4.3597447222071 × 10⁻¹⁸ | J |

All values are CODATA 2018 or exact SI definitions.

> **In plain words.** These are the fixed numbers. You will rarely need them
> directly, because the conversion table above already includes them.

## Open questions

- Should this card be generated from a machine-readable source (e.g. `scipy.constants`)
  to avoid transcription errors? Probably yes once the code exists.
- Does the project need to support atomic units natively, or can everything be
  converted at the boundary? Convert at the boundary is simpler.

## What would change this document

- A change in the CODATA recommended values (they are stable to the precision
  used here).
- Adoption of a different internal unit convention by the main libraries.

## Sources

1. CODATA 2018 recommended values of the fundamental physical constants.
   <https://physics.nist.gov/cuu/Constants/> (retrieved 2026-11-07).
2. NIST-JANAF Thermochemical Tables (unit conventions).
   <https://janaf.nist.gov/> (retrieved 2026-11-07).
3. IUPAC, *Quantities, Units and Symbols in Physical Chemistry* (the Green
   Book), 3rd ed., RSC (2007).
4. Atomic Simulation Environment documentation, units and file formats.
   <https://wiki.fysik.dtu.dk/ase/> (retrieved 2026-11-07).
