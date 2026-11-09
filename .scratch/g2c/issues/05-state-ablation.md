# 05: State ablation (V1 vs stateless)

**What to build:** Train NPA with state_dims=0 (no hidden channels) on the same world. Compare rollout drift to Ticket 04's result. This is the G2 question at multi-particle scale.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] Both models trained and evaluated
- [ ] Comparison reported with statistical significance (>=3 seeds)
- [ ] Clear verdict: state helps / doesn't help / inconclusive
