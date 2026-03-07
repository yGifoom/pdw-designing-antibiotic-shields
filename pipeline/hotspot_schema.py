from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional


HotspotMode = Literal["manual", "auto", "hybrid"]


@dataclass
class ManualResidueList:
    chain: str
    residues: List[int]
    label: str


@dataclass
class ManualResidueRange:
    chain: str
    start: int
    end: int
    label: str


@dataclass
class ManualSphere:
    center_xyz: List[float]
    radius: float
    label: str


@dataclass
class HotspotWeights:
    pocket: float = 1.0
    pesto: float = 1.0
    conservation: float = 0.8
    catalytic_prior: float = 0.6
    ligand_context: float = 0.7
    exposure_persistence: float = 1.0


DEFAULT_KEEP_RULES: Dict[str, float] = {
    "min_total_score": 0.45,
    "min_patch_size": 4,
}


def merge_sources(manual_ids: List[str], auto_ids: List[str]) -> List[Dict[str, Optional[str]]]:
    merged = [{"hotspot_id": h, "source": "manual"} for h in manual_ids]
    merged.extend({"hotspot_id": h, "source": "auto"} for h in auto_ids if h not in manual_ids)
    return merged
