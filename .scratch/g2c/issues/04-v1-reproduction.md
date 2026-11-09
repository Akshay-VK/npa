# 04: V1 reproduction at small N

**What to build:** Train V1 (NPA-faithful, state_dims=16) on the harmonic+spring world. Evaluate rollout drift, energy conservation, stability on held-out world.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Rollout drift < 5% over 100 steps on held-out world
- [ ] Energy drift < 1% over 1000 steps
- [ ] Training converges (loss decreases monotonically)
