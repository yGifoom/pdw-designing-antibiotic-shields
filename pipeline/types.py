from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StageResources:
    cpu: int = 2
    memory_gb: int = 8
    gpu: int = 0
    walltime_min: int = 60


@dataclass
class StageSpec:
    key: str
    order: int
    module: str
    image: str
    resources: StageResources
    enabled: bool = True


@dataclass
class StageContext:
    run_id: str
    scratch_root: Path
    run_root: Path
    stage_dir: Path
    config: Dict[str, Any]
    stage_spec: StageSpec


@dataclass
class StageResult:
    stage_key: str
    success: bool
    message: str = ""
    outputs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    skipped: bool = False


@dataclass
class CandidateRecord:
    candidate_id: str
    run_id: str
    conformer_id: Optional[str] = None
    hotspot_id: Optional[str] = None
    hotspot_source: Optional[str] = None
    sequence_branch: Optional[str] = None
    parent_backbone_id: Optional[str] = None
    first_pass_parent: Optional[str] = None
    second_pass_parent: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
