---
status: draft
confidence: medium
last_verified: 2026-11-07
depends_on: [01-landscape-and-taxonomy.md]
---

# Software and tooling ecosystem

The libraries, codes, and file formats the project will actually use. This is
not a survey of every available package — it is the minimal stack required to
run experiments, and the reason for each choice.

**Bottom line**

- **ASE (Atomic Simulation Environment)** is the primary interface: it provides
  a uniform calculator API, trajectory I/O, and a Python- first workflow.
- **PySCF** is the quantum chemistry engine for any DFT/CC calls, because it is
  Python-friendly, MIT-licensed, and supports gradients and properties.
- **ASE + PySCF** are the bridge: the project energy function will be implemented
  as a PySCF calculator wrapped by ASE, so that a single code does both the
  reference data generation and the model evaluation.
- **jraph / Elegy / Equinox** are the ML frameworks under consideration. The
  choice depends on whether the model is invariant (Equinox + MLP) or
  equivariant (Elegy + NequIP/MACE). For a small team, Equinox is the lightest
  dependency.
- **ASE, PySCF, and Equinox** are the minimum stack. Nothing else is required
  for phases 0–3. Enhanced sampling (metadynamics) requires **PLUMED**, which
  interfaces through ASE.
- **Docker** (or singularity) for containerisation, with a `Dockerfile` that
  installs the stack and sets the random seed. This is the reproducibility
  artefact.

## The minimum stack

| Component | Purpose | Install | Why this one |
|---|---|---|---|
| **ASE** | Calculator API, trajectories, units | `pip install ase` | Python- first, supports PySCF calculator, handles XYZ/Extended XYZ trajectories. |
| **PySCF** | DFT, HF, MP2, CC, gradients | `pip install pyscf` | MIT-licensed, supports def2 basis sets via interfaces, good gradient support. |
| **Equinox** | Small NN library (invariant) | `pip install equinox` | Minimal dependency (just JAX), functional style, good for MLP potentials. |
| **PLUMED** | Enhanced sampling (metadynamics, etc.) | system package (apt install plumed) | Interfaces through ASE; needed for phase 4 free-energy profiles. |
| **Docker** | Reproducibility container | `docker build .` | Seals the stack version, OS, and random seed; the reproducibility artefact. |

> **In plain words.** The project does not need every ML library. One calculator
> (PySCF), one ML framework (Equinox), one simulation interface (ASE), and one
> container (Docker) are enough for phases 0–3. Add PLUMED for free-energy
> profiles in phase 4.

## Calculator interface

The project will implement its energy-based potential as a PySCF calculator:

```python
from ase.calculators.pyscf import PySCF

class NPACalculator(PySCF):
    def __init__(self, model, mol, cutoff=5.0):
        super().__init__(mol)  # init PySCF with the ASE molecule
        self.model = model      # the Equinox/JAX model
        self.cutoff = cutoff    # neighbour list cutoff
```

This gives us:

- **Energy and forces** via automatic differentiation through PySCF.
- **Single-point timing** in the same protocol as the challenge (def2-QZVP, CPU).
- **Trajectory output** through ASE (`ase.trajectories.TrajFile`).
- **Seamless integration** with the rest of the ASE ecosystem (thermostats,
  optimizers, etc.).

> **In plain words.** We write one class that translates between the project's
> neural network and PySCF's quantum chemistry. This gives us energies, forces,
> and gradients for the cost of writing about 30 lines of code.

## ML framework choice

For phases 0–3, the project will use **Equinox** (JAX-based) for two reasons:

1. **Light dependencies.** Equinox is a thin wrapper around JAX. No heavy C++
   compilers, no CUDA toolkit requirements at install time.
2. **Functional style.** Equinox encourages pure functions, which makes it easy
   to reason about the model's behaviour across rollouts and to write unit tests.

If the project later decides to use an equivariant architecture (MACE-style), the
switch is to **Elegy** or **jraph**, but that is a phase-4 decision, not a
phase-0 requirement.

> **In plain words.** Start simple: Equinox + JAX. If we need equivariance
> later, we switch frameworks. Do not start with the heaviest framework.

## Trajectory format

The project will use **ASE `ExtxyzTrajectory`** format:

- **Positions** (Å)
- **Forces** (eV/Å)
- **Energy** (eV)
- **Timestep** (fs) as user comment
- **Timestep index** as user comment

Readable by ASE, LAMMPS, and ViJEST. Self-describing: the units and contents
are in the file headers.

> **In plain words.** The trajectory file is the primary artefact. It contains
> everything needed to replay the experiment: positions, forces, energy, and the
> timestep. If it is not in the file, it is not part of the experiment.

## Enhanced sampling

For phase 4 (free-energy profiles), the project will use **PLUMED** through ASE:

- PLUMED metadynamics bias added through ASE's `ASECalculatorWith`.
- Bias deposited every `N` steps.
- WHAM/MBAR reweighting through ASE's analysis tools.

> **In plain words.** Metadynamics is the chosen enhanced-sampling method. It
> requires PLUMED, which we install as a system package and use through ASE.

## Containerisation

The reproducibility artefact is a **Dockerfile** that:

1. Installs Python 3.11.
2. Installs ASE, PySCF, Equinox, and their dependencies.
3. Copies the project code and config.
4. Sets the random seed via an environment variable.
5. Defines the entrypoint: `python -m project.run --config config.yaml`.

The Docker image is built and pushed after every phase gate. The image tag
encodes the phase and version: `npa:v0.1-G0`, `npa:v0.2-G2`, etc.

> **In plain words.** The Docker container is the reproducibility insurance.
> If someone cannot reproduce the result from the Dockerfile + config, the
> result is not reproducible.

## What we do not use (and why)

| Component | Why not |
|---|---|
| **TensorFlow / PyTorch** | The project uses JAX/Equinox. Starting with another framework creates unnecessary migration cost. |
| **LAMMPS** | ASE can do everything LAMMPS does for this project's length scales, and ASE's Python interface is more convenient for experimentation. |
| **Gaussian / ORCA** | PySCF is free, open source, and supports the basis sets we need. Proprietary codes are not reproducible for a small-team project. |
| **CuPy** | JAX handles GPU execution natively. CuPy would be an extra dependency without a clear benefit for the phase-0–3 stack. |

> **In plain words.** The stack is minimal by design. Every addition is a
> maintenance burden. If it is not needed for phases 0–3, it is not installed.

## Open questions

- Should the project use JAX’s `torch.jit` compatibility to import pretrained
  PyTorch models? This would be a phase-4 consideration.
- Does the project need GPU support in the Docker container from the start, or
  can it be added when the trajectory cost model shows a need?
- Is PLUMED's licence compatible with the project's licensing goals? It is
  BSD-3-clause, which is compatible with MIT and most project licences.

## What would change this document

- A decision to use an equivariant framework (MACE, NequIP) as the primary
  framework, which would change the ML framework, calculator bridge, and
  dependency profile.
- Release of a new version of ASE or PySCF that breaks the calculator
  interface, which would require a short adapter.
- A collaboration that already uses a different stack, which would be evaluated
  on its merits.

## Sources

1. Atomic Simulation Environment documentation.
   <https://wiki.fysik.dtu.dk/ase/> (retrieved 2026-11-07).
2. PySCF developer team, *PySCF: An open-source quantum chemistry research
   code*, J. Chem. Phys. 155, 204104 (2021).
   <https://doi.org/10.1063/5.0012369> (retrieved 2026-11-07).
3.nikov et al., *Equinox: A neural network library for JAX*, 2020.
   <https://github.com/deepmind/equinox> (retrieved 2026-11-07).
4. PLUMED consortium, *PLUMED 2: a software package for free-energy
   calculations using metadynamics, free-energy perturbation,
   and umbrella sampling, well-tempered metadynamics*, Comput. Phys.
   Commun. 196, 119 (2015).
   <https://doi.org/10.1016/j.cpc.2015.04.009> (retrieved 2026-11-07).
5. Sesé and Bihlmayer, *Docker for reproducible research*, arXiv:1907.03266.
   <https://arxiv.org/abs/1907.03266> (retrieved 2026-11-07).