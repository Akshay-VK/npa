"""Metrics and the physics test battery. Shared by every variant."""

from __future__ import annotations


def energy_mae(pred, ref) -> float:
    raise NotImplementedError("v0.0")


def force_mae(pred, ref) -> float:
    raise NotImplementedError("v0.0")


def barrier_error(pred, ref) -> float:
    raise NotImplementedError("v0.0")


def rollout_drift(trajectory) -> float:
    raise NotImplementedError("v0.0")