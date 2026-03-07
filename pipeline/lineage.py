from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from pipeline.diagnostics import write_csv


LINEAGE_COLUMNS = [
    "candidate_id",
    "run_id",
    "conformer_id",
    "hotspot_id",
    "hotspot_source",
    "hotspot_component_scores",
    "parent_backbone_id",
    "sequence_design_branch",
    "first_pass_parent",
    "second_pass_parent",
    "pTM",
    "ipTM",
    "ipSAE",
    "ipSAE_pass",
    "pose_retention",
    "interface_geometry",
    "fold_occupancy",
    "helix_occupancy",
    "sheet_occupancy",
    "radius_compactness",
    "competing_fold_basins",
    "esm_score",
    "final_rank",
    "artifact_paths",
]


def write_lineage(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    normalized: List[Dict[str, object]] = []
    for row in rows:
        normalized.append({col: row.get(col, "") for col in LINEAGE_COLUMNS})
    write_csv(path, normalized)
