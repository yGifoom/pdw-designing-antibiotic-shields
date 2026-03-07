from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from pipeline.config import PipelineConfig, StageConfig


@dataclass(slots=True)
class StageDefinition:
    name: str
    description: str
    default_image_key: str
    dependencies: List[str] = field(default_factory=list)
    default_fast_params: Dict[str, object] = field(default_factory=dict)
    default_thorough_params: Dict[str, object] = field(default_factory=dict)


STAGES: List[StageDefinition] = [
    StageDefinition("01_prepare_target", "prepare target", "orchestrator"),
    StageDefinition("02_define_hotspots", "manual hotspot load/validation", "orchestrator", ["01_prepare_target"]),
    StageDefinition("03_rfd3_backbones", "RFdiffusion3 backbone generation", "rfd3", ["02_define_hotspots"], {"num_backbones": 32}, {"num_backbones": 256}),
    StageDefinition("04_ligandmpnn_design", "LigandMPNN sequence design", "ligandmpnn", ["03_rfd3_backbones"], {"seqs_per_backbone": 4}, {"seqs_per_backbone": 16}),
    StageDefinition("05_af3_score_pass1", "AF3 scoring pass 1", "af3", ["04_ligandmpnn_design"], {"max_candidates": 128}, {"max_candidates": 2048}),
    StageDefinition("06_rank_cluster_filter_pass1", "first-pass ranking/clustering/filtering", "orchestrator", ["05_af3_score_pass1"], {"cluster_aggressiveness": "high", "shortlist": 12}, {"cluster_aggressiveness": "medium", "shortlist": 64}),
    StageDefinition("07_optional_rediffusion", "optional second-pass hit expansion", "rfd3", ["06_rank_cluster_filter_pass1"], {"enabled": False, "expansion_per_family": 2}, {"enabled": True, "expansion_per_family": 8}),
    StageDefinition("08_redesign_sequences", "redesign sequences after rediffusion", "ligandmpnn", ["07_optional_rediffusion"], {"seqs_per_backbone": 2}, {"seqs_per_backbone": 8}),
    StageDefinition("09_af3_rescore_pass2", "AF3 rescoring post-rediffusion", "af3", ["08_redesign_sequences"], {"max_candidates": 64}, {"max_candidates": 512}),
    StageDefinition("10_esm_annotation", "final ESM naturalness annotation", "orchestrator", ["09_af3_rescore_pass2"]),
    StageDefinition("11_final_rank_report", "final ranking/report generation", "orchestrator", ["10_esm_annotation"]),
]


def resolve_stage_config(cfg: PipelineConfig, stage: StageDefinition) -> StageConfig:
    base_params = stage.default_fast_params if cfg.preset == "fast" else stage.default_thorough_params
    override = cfg.stage_overrides.get(stage.name, StageConfig())

    image = override.image
    if image is None:
        image = getattr(cfg.images, stage.default_image_key)

    merged_params = {**base_params, **override.params}
    return StageConfig(
        enabled=override.enabled,
        image=image,
        cpu=override.cpu,
        memory=override.memory,
        gpu=override.gpu,
        timeout_minutes=override.timeout_minutes,
        params=merged_params,
    )
