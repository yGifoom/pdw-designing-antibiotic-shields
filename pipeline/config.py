from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Mapping, Optional

from pipeline.simple_yaml import load_yaml_lite


PresetName = Literal["fast", "thorough"]


@dataclass(slots=True)
class ClusterConfig:
    project: str
    namespace: str
    scratch_mount: str = "/mnt/scratch"
    shared_ro_mount: str = "/mnt/shared-ro"
    scratch_pvc: str = "pdw-scratch-pvc"
    shared_ro_pvc: str = "pdw-shared-ro-pvc"
    shared_ro_subpath: Optional[str] = None


@dataclass(slots=True)
class ImageCatalog:
    rfd3: str
    ligandmpnn: str
    af3: str
    orchestrator: str = "python:3.11-slim"


@dataclass(slots=True)
class GlobalThresholds:
    pTM_min: float = 0.65
    ipTM_min: float = 0.6
    ipSAE_min: float = 0.55
    clash_free_required: bool = True


@dataclass(slots=True)
class RankingWeights:
    pTM: float = 0.2
    ipTM: float = 0.3
    ipSAE: float = 0.3
    pose_retention: float = 0.1
    interface_geometry_agreement: float = 0.05
    esm_naturalness: float = 0.05


@dataclass(slots=True)
class StageConfig:
    enabled: bool = True
    image: Optional[str] = None
    cpu: int = 4
    memory: str = "16Gi"
    gpu: int = 1
    timeout_minutes: int = 240
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PipelineConfig:
    run_id: str
    preset: PresetName
    scratch_root: Path
    target_input: Path
    hotspots_file: Optional[Path]
    cluster: ClusterConfig
    images: ImageCatalog
    thresholds: GlobalThresholds = field(default_factory=GlobalThresholds)
    ranking_weights: RankingWeights = field(default_factory=RankingWeights)
    stage_overrides: Dict[str, StageConfig] = field(default_factory=dict)


class ConfigError(ValueError):
    pass


def _require_keys(data: Mapping[str, Any], section: str, keys: list[str]) -> None:
    for key in keys:
        if key not in data:
            raise ConfigError(f"Missing `{section}.{key}` in config")


def _load_stage_overrides(raw: Mapping[str, Any]) -> Dict[str, StageConfig]:
    out: Dict[str, StageConfig] = {}
    for stage_name, cfg in raw.items():
        out[stage_name] = StageConfig(
            enabled=cfg.get("enabled", True),
            image=cfg.get("image"),
            cpu=cfg.get("cpu", 4),
            memory=cfg.get("memory", "16Gi"),
            gpu=cfg.get("gpu", 1),
            timeout_minutes=cfg.get("timeout_minutes", 240),
            params=cfg.get("params", {}),
        )
    return out


def load_config(path: Path) -> PipelineConfig:
    with path.open("r", encoding="utf-8") as f:
        raw = load_yaml_lite(f.read())

    if not isinstance(raw, dict):
        raise ConfigError("Top-level YAML must be a mapping")

    _require_keys(raw, "root", ["run_id", "preset", "scratch_root", "target_input", "cluster", "images"])

    cluster = raw["cluster"]
    images = raw["images"]
    _require_keys(cluster, "cluster", ["project", "namespace", "scratch_pvc", "shared_ro_pvc"])
    _require_keys(images, "images", ["rfd3", "ligandmpnn", "af3"])

    if raw["preset"] not in {"fast", "thorough"}:
        raise ConfigError("preset must be one of: fast, thorough")

    thresholds_raw = raw.get("thresholds", {})
    ranking_raw = raw.get("ranking_weights", {})

    return PipelineConfig(
        run_id=str(raw["run_id"]),
        preset=raw["preset"],
        scratch_root=Path(raw["scratch_root"]),
        target_input=Path(raw["target_input"]),
        hotspots_file=Path(raw["hotspots_file"]) if raw.get("hotspots_file") else None,
        cluster=ClusterConfig(
            project=cluster["project"],
            namespace=cluster["namespace"],
            scratch_mount=cluster.get("scratch_mount", "/mnt/scratch"),
            shared_ro_mount=cluster.get("shared_ro_mount", "/mnt/shared-ro"),
            scratch_pvc=cluster["scratch_pvc"],
            shared_ro_pvc=cluster["shared_ro_pvc"],
            shared_ro_subpath=cluster.get("shared_ro_subpath"),
        ),
        images=ImageCatalog(
            rfd3=images["rfd3"],
            ligandmpnn=images["ligandmpnn"],
            af3=images["af3"],
            orchestrator=images.get("orchestrator", "python:3.11-slim"),
        ),
        thresholds=GlobalThresholds(**thresholds_raw),
        ranking_weights=RankingWeights(**ranking_raw),
        stage_overrides=_load_stage_overrides(raw.get("stage_overrides", {})),
    )
