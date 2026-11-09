"""Synthetic worlds. Generated on the fly; no storage, no download.

The held-out world (different barrier height / coupling) is generated here too,
so a model cannot memorise the training world.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import torch


@dataclass
class World:
    kind: str
    seed: int
    x: torch.Tensor
    v: torch.Tensor | None = None


def make_world(kind: Literal["double_well", "two_channel", "harmonic"], n: int, seed: int) -> World:
    raise NotImplementedError("v0.0")