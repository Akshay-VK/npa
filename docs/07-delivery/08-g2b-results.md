---
status: draft
confidence: medium
last_verified: 2026-11-09
depends_on: [05-g0-foundations-result.md, 07-g1-g2-results.md]
---

# G2b — non-conservative dynamics: does state help?

## Result: negative (state doesn't help, even when it should)

Tested on a damped double well (Langevin dynamics: friction γ=0.5, temperature kT=0.1).
Force = -dU/dx - γ·v. Held-out world uses γ=0.6, barrier=1.3.

| Model | force MAE | rollout drift | Notes |
|---|---|---|---|
| V2 (stateless, position only) | 0.2443 | 0.2098 | Learns conservative force; misses friction |
| DirectWithVelocity (stateless, pos+vel) | **0.1876** | **0.1969** | Velocity helps; friction is learnable |
| V3b (stateful, single-net) | 1.7180 | 4.2206 | State doesn't help; much worse |
| Ablation (V3b, frozen state) | 3.0582 | 8.8306 | Out of distribution; inconclusive |

**Key finding.** Velocity information *does* help (0.188 < 0.244): a model that sees velocity learns friction. But V3b's *learned* latent state does *not* help (1.718 >> 0.244). The state mechanism is the bottleneck, not the concept.

The latent state tracks velocity (correlation r ≈ 0.6 in G2, improved to r ≈ 0.99 after single-network restructure), but the force prediction doesn't exploit it. The state encoding works; the state *usage* doesn't.

**Plain words.** We made the spring sticky (friction) so that a model with memory should win — it can encode "how fast is the ball moving" and predict the friction force. A model that directly sees velocity does win (0.19 vs 0.24). But our memory model loses badly (1.72), even though its memory does track velocity. The memory is there and working, but the network can't figure out how to use it for prediction. The problem is the wiring, not the concept.

## What this means for the project

G2b is a **negative result** on the state mechanism. The hypothesis "persistent latent state helps for dynamics" is not supported by this experiment. Two interpretations:

1. **The state encoding is the problem.** The state update (step_state) learns to track velocity, but the force network doesn't learn to use it. The credit assignment (force loss → state update) is too indirect.
2. **The concept is sound but the implementation is wrong.** A model that directly receives velocity works. The learned-state version should be able to match it, given better training (supervised state update, or a different architecture).

**Recommendation.** Before pivoting, try one more experiment: supervise the state update to predict velocity explicitly (auxiliary loss), then check if the force network can use it. If that still fails, the state mechanism is fundamentally limited and we should pivot to the benchmark route.

## Open questions

- Can a supervised state update (h trained to predict v) close the gap?
- Does the state mechanism work on a simpler system (e.g., velocity → force with no spatial dependence)?
- Is the gap due to the state representation (8 dims) or the force network's inability to use it?

## Sources

1. Project measurements: `runs/g2b/results.json`.
2. Code: `code/g2b_experiment.py`, `code/g2b_control.py`.