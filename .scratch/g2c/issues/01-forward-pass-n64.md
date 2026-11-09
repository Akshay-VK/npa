# 01: Forward pass at N=64

**What to build:** A script that loads the official NPA model with the CPU shim, creates a 64-particle state, runs one forward pass, and reports timing + peak RSS. Proves the perception pipeline works at multi-particle scale on this laptop.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Forward pass completes without error
- [ ] Timing < 1s per step at N=64
- [ ] Peak RSS < 2 GB
