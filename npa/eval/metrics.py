"""Metrics and the physics test battery."""

from __future__ import annotations

import math

import torch


def energy_mae(pred: torch.Tensor, ref: torch.Tensor) -> float:
    return (pred - ref).abs().mean().item()


def force_mae(pred: torch.Tensor, ref: torch.Tensor) -> float:
    return (pred - ref).abs().mean().item()


def barrier_error(pred_energy: torch.Tensor, x_grid: torch.Tensor, ref_barrier: float) -> float:
    """Error in estimated barrier height (max E - min E on grid)."""
    pred_barrier = (pred_energy.max() - pred_energy.min()).item()
    return abs(pred_barrier - ref_barrier)


def rollout_drift(pred_traj: torch.Tensor, ref_traj: torch.Tensor) -> float:
    """Mean absolute deviation over a rollout, normalised by trajectory amplitude."""
    amp = (ref_traj.max() - ref_traj.min()).item()
    if amp < 1e-8:
        return float("inf")
    return (pred_traj - ref_traj).abs().mean().item() / amp