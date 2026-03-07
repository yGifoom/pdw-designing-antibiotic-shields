from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


PRESETS: Dict[str, Dict[str, Any]] = {
    "fast": {
        "bioemu": {"target_samples": 80, "candidate_samples": 60, "representatives": 10},
        "hotspot": {"max_hotspots": 8},
        "generation": {"num_backbones": 64},
        "af3": {"max_candidates_first_pass": 120},
        "rediffusion": {"enabled": True, "seed_count": 12},
        "sanity": {"shortlist": 40},
    },
    "thorough": {
        "bioemu": {"target_samples": 500, "candidate_samples": 250, "representatives": 40},
        "hotspot": {"max_hotspots": 30},
        "generation": {"num_backbones": 500},
        "af3": {"max_candidates_first_pass": 1000},
        "rediffusion": {"enabled": True, "seed_count": 80},
        "sanity": {"shortlist": 250},
    },
}


def deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def apply_preset(config: Dict[str, Any]) -> Dict[str, Any]:
    preset = config.get("preset", "fast")
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}', expected one of {sorted(PRESETS)}")
    return deep_merge(PRESETS[preset], config)
