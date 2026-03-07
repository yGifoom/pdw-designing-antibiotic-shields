from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.types import StageSpec


@dataclass
class SubmissionResult:
    backend: str
    stage: str
    command: str
    script_path: str


class ClusterBackend:
    def submit(self, stage: StageSpec, run_root: Path, command: str) -> SubmissionResult:
        raise NotImplementedError


class LocalBackend(ClusterBackend):
    def submit(self, stage: StageSpec, run_root: Path, command: str) -> SubmissionResult:
        return SubmissionResult(backend="local", stage=stage.key, command=command, script_path="")
