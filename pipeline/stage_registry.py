from __future__ import annotations

from typing import List

from pipeline.types import StageResources, StageSpec


STAGE_ORDER = [
    "01_prepare_target",
    "02_bioemu_generate",
    "03_bioemu_cluster",
    "04_hotspot_detect",
    "05_hotspot_select",
    "06_generate_backbones",
    "07_design_seq_ligandmpnn",
    "08_design_seq_carbonara",
    "09_af3_score",
    "10_rank_first_pass",
    "11_select_rediffusion_seeds",
    "12_rediffusion",
    "13_seq_redesign",
    "14_af3_rescore",
    "15_bioemu_candidate_sanity",
    "16_esm_annotate",
    "17_final_rank",
    "18_report",
]


def build_stage_specs(config: dict) -> List[StageSpec]:
    specs: List[StageSpec] = []
    for idx, key in enumerate(STAGE_ORDER, start=1):
        stage_cfg = config["stages"].get(key, {})
        specs.append(
            StageSpec(
                key=key,
                order=idx,
                module=f"stages.{key}",
                image=stage_cfg.get("image", "TODO/stage-image"),
                resources=StageResources(**stage_cfg.get("resources", {})),
                enabled=stage_cfg.get("enabled", True),
            )
        )
    return specs


def select_stage_window(keys: List[str], start: str | None, end: str | None) -> List[str]:
    if start and start not in keys:
        raise ValueError(f"Unknown start stage: {start}")
    if end and end not in keys:
        raise ValueError(f"Unknown end stage: {end}")
    sidx = keys.index(start) if start else 0
    eidx = keys.index(end) if end else len(keys) - 1
    if sidx > eidx:
        raise ValueError("start-stage must come before end-stage")
    return keys[sidx : eidx + 1]
