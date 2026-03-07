from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from pipeline.presets import apply_preset


REQUIRED_TOP_LEVEL = [
    "preset",
    "target",
    "hotspot",
    "af3",
    "ranking",
    "stages",
    "cluster",
]


def _load_yaml_compatible(path: Path) -> Dict[str, Any]:
    """Load configuration from YAML-compatible JSON.

    This repository keeps `.yaml` configs in strict JSON syntax so they remain valid YAML
    while avoiding external parser dependencies in constrained cluster bootstrap contexts.
    """
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(path: Path) -> Dict[str, Any]:
    raw = _load_yaml_compatible(path)
    if not isinstance(raw, dict):
        raise ValueError("Configuration must be a mapping")
    for key in REQUIRED_TOP_LEVEL:
        if key not in raw:
            raise ValueError(f"Missing required top-level config key: {key}")
    cfg = apply_preset(raw)
    validate_config(cfg)
    return cfg


def validate_config(config: Dict[str, Any]) -> None:
    mode = config.get("hotspot", {}).get("mode")
    if mode not in {"manual", "auto", "hybrid"}:
        raise ValueError("hotspot.mode must be one of: manual, auto, hybrid")

    for stage_key, stage_cfg in config.get("stages", {}).items():
        gpu = stage_cfg.get("resources", {}).get("gpu", 0)
        if gpu not in (0, 1):
            raise ValueError(f"Stage {stage_key} must request 0 or 1 GPU, found {gpu}")


def snapshot_config(config: Dict[str, Any], run_root: Path) -> Path:
    out_path = run_root / "config.snapshot.yaml"
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
    json_path = run_root / "run_manifest.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump({"config_keys": sorted(config.keys())}, handle, indent=2)
    return out_path
