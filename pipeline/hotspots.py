from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Union

from pipeline.simple_yaml import load_yaml_lite


HotspotMode = Literal["residue_list", "residue_range", "center_radius", "chain_residues"]


@dataclass(slots=True)
class HotspotRecord:
    hotspot_id: str
    label: str
    source: str
    mode: HotspotMode
    payload: Dict[str, Any]


def load_hotspots(path: Path) -> List[HotspotRecord]:
    with path.open("r", encoding="utf-8") as f:
        data = load_yaml_lite(f.read())
    if not isinstance(data, dict) or "hotspots" not in data:
        raise ValueError("hotspots file must contain top-level `hotspots` list")

    records: List[HotspotRecord] = []
    for idx, item in enumerate(data["hotspots"]):
        if not isinstance(item, dict):
            raise ValueError(f"hotspot[{idx}] must be a mapping")
        mode = item.get("mode")
        if mode not in {"residue_list", "residue_range", "center_radius", "chain_residues"}:
            raise ValueError(f"hotspot[{idx}] invalid mode={mode}")
        records.append(
            HotspotRecord(
                hotspot_id=str(item["hotspot_id"]),
                label=str(item.get("label", item["hotspot_id"])),
                source=str(item.get("source", "manual")),
                mode=mode,
                payload=item.get("payload", {}),
            )
        )
    return records
