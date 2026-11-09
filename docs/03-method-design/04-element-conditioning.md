---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: []
---

# Element conditioning and the per-element-network misconception

The source note correctly favours shared learning, but overstates a conservation objection to per-element networks. The important boundary is between independently predicting incompatible forces and jointly differentiating a common total energy.

**Key takeaways**

- Use shared element conditioning as the default experimental baseline.
- Joint per-element energy networks can be physically consistent.
- A new embedding does not confer competence on a new element.

## Element identity is physical information

Atomic number $Z_i$ determines nuclear charge; isotope mass affects nuclear dynamics separately. A learned embedding $e(Z_i)$ is a statistical representation of that identity. It is not inherently smooth across the periodic table: neighbouring integer labels need not have neighbouring learned vectors or similar chemistry. Fixed descriptors such as valence and radius introduce additional assumptions and data dependencies.

For a proposed shared model, use $e(Z_i)$ in node features and ensure interaction messages see both sender and receiver identities. The total charge and electronic-state specification are system-level inputs. Atom-specific partial charges are predictions under a particular partitioning convention, not synonyms for nuclear charge. Geometry supplies directional information; “orientation” should not be a fixed elemental attribute.

> **In plain words.** An element label tells the model what kind of nucleus it is looking at. It does not tell it which way the molecule points. Giving a student a new label on an empty notebook does not teach the chemistry of that element.

## A constructive counterexample to the source note

Consider jointly trained elemental energy networks,
$$E(R,Z)=\sum_i f_{Z_i}(D_i(R,Z)),$$
where $D_i$ is an invariant environment descriptor containing neighbouring element identities. Define all nuclear forces by differentiating this total energy. The resulting model can be translationally and rotationally invariant, conservative, and consistent across mixed-element environments. It need not have a shared trunk. Element-specific atomic networks are part of the established high-dimensional neural-potential lineage [QEQ].

For a pair-only illustration, choose a symmetric energy $u_{ab}(r)=u_{ba}(r)$ for element types $a,b$ and distance $r$. Summing each unordered pair once and differentiating produces equal-and-opposite pair forces. Whether the code uses separate type-specific modules is immaterial to that argument.

The source note's problematic case is separate force or update rules trained without a common energy or joint coupling contract. They can violate integrability or momentum balance. Neither sharing weights nor supplying embeddings repairs that automatically. This distinction changes the ablation: compare valid energy-based alternatives before comparing deliberately unconstrained dynamics.

> **In plain words.** Different specialists can write different chapters of one consistent rulebook. Trouble begins when each specialist independently invents a conflicting rule for the same encounter. The number of specialists is not the underlying physics problem.

## Fair architecture comparison

Compare a shared trunk plus embeddings, a shared trunk plus element-specific heads, and separate jointly trained elemental energy networks. Hold the scalar-energy output, geometry descriptors, data splits and optimisation budget fixed. Report both fixed-total-parameter and fixed-per-element-capacity comparisons where feasible: these answer different efficiency questions. Rare elements require a per-element error report and data-count table. A shared model can suffer negative transfer; a separate model can waste data. Those are empirical questions, not symmetry theorems.

Keep unseen combinations distinct from unseen elements. Testing a new C–O environment when both elements were trained is different from testing aluminium after training only organic elements. Unsupported atomic numbers should trigger an explicit error. **Recommendation (inference):** use shared conditioning first for reuse and lower maintenance, then test separate energy networks as a legitimate control.

> **In plain words.** Give every design the same examination and study budget. Record which subjects had few examples. A student seeing a new combination of familiar ideas faces a different task from seeing an entirely new subject.

## Edge cases that force clarity

Test a mixed-element dimer under atom permutation, separated fragments, an isotopically substituted system, a charged molecule and an unsupported atomic number. Under an isotope substitution the same electronic PES is normally used within the Born–Oppenheimer approximation while masses change the trajectory. Under a change in total charge the PES generally changes. These cases expose accidental mixing of element identity, mass and electronic state.

> **In plain words.** Replacing a ball with a heavier ball can change its motion without changing the shape of the ramp. Changing electrical charge can change the ramp itself. The model should keep these ideas separate.

## Open questions

- Which elements and charge states are in the first deployment domain?
- Does a shared model reduce rare-element error at matched cost?

> **In plain words.** These are choices that the current evidence does not settle. Write down the answer before spending money on an experiment that depends on it. An empty result is better than an invented answer.

## What would change this document

- Measured negative transfer or strong element-specific capacity requirements.
- A validated physical descriptor transfer study.

> **In plain words.** Treat this document like a map made before the expedition. New measurements can reveal a better route. Record what changed and why when that happens.

## Sources

- [Ko et al., fourth-generation neural potentials, full paper](https://arxiv.org/html/2009.06484) (retrieved 2026-11-07).
- [Batzner et al., NequIP](https://arxiv.org/abs/2101.03164) (retrieved 2026-11-07).
