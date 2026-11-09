# 02: Multi-particle world + trajectory generation

**What to build:** `npa/data/multiparticle.py` — N particles in a 2D harmonic well with pairwise springs. Generates deterministic trajectories via velocity Verlet. Held-out variant (different k, spring_k). Tests for energy conservation.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Trajectory generation produces stable, energy-conserving orbits
- [ ] Held-out world differs in parameters
- [ ] Energy drift < 0.1% over 1000 steps
