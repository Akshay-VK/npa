"""One training loop for every variant. Config in, Run out."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Run:
    out_dir: Path
    metrics: dict


def train(config: dict, model, data) -> Run:
    """Train `model` on `data` per `config`. Writes config.yaml, git_sha, metrics.json, ckpt.pt."""
    raise NotImplementedError("v0.0")