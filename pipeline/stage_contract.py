from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


MANDATORY_STAGE_FILES = [
    "status.json",
    "params.json",
    "metrics.json",
    "provenance.json",
    "stdout.log",
    "stderr.log",
    "summary.csv",
    "validation.json",
]


@dataclass(slots=True)
class StageContext:
    run_id: str
    stage_name: str
    run_root: Path

    @property
    def stage_dir(self) -> Path:
        return self.run_root / self.stage_name


def iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def ensure_stage_dir(ctx: StageContext) -> Path:
    ctx.stage_dir.mkdir(parents=True, exist_ok=True)
    return ctx.stage_dir


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_summary_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({k for row in rows for k in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def stage_completed(stage_dir: Path) -> bool:
    return all((stage_dir / name).exists() for name in MANDATORY_STAGE_FILES) and json.loads((stage_dir / "status.json").read_text(encoding="utf-8")).get("state") == "completed"


def validate_stage_outputs(stage_dir: Path) -> Dict[str, Any]:
    missing = [name for name in MANDATORY_STAGE_FILES if not (stage_dir / name).exists()]
    valid = len(missing) == 0
    return {
        "valid": valid,
        "missing_files": missing,
        "checked_at": iso_now(),
    }


def initialize_stage(ctx: StageContext, params: Mapping[str, Any], provenance: Mapping[str, Any]) -> None:
    ensure_stage_dir(ctx)
    write_json(ctx.stage_dir / "status.json", {"state": "running", "started_at": iso_now()})
    write_json(ctx.stage_dir / "params.json", params)
    write_json(ctx.stage_dir / "provenance.json", {**provenance, "created_at": iso_now()})
    (ctx.stage_dir / "stdout.log").touch()
    (ctx.stage_dir / "stderr.log").touch()


def finalize_stage(
    ctx: StageContext,
    metrics: Mapping[str, Any],
    summary_rows: List[Mapping[str, Any]],
    extra_validation: Mapping[str, Any] | None = None,
) -> None:
    write_json(ctx.stage_dir / "metrics.json", metrics)
    write_summary_csv(ctx.stage_dir / "summary.csv", summary_rows)
    write_json(ctx.stage_dir / "validation.json", {"state": "pending", "checked_at": iso_now()})
    validation = validate_stage_outputs(ctx.stage_dir)
    if extra_validation:
        validation = {**validation, **extra_validation}
    write_json(ctx.stage_dir / "validation.json", validation)
    write_json(
        ctx.stage_dir / "status.json",
        {
            "state": "completed" if validation["valid"] else "failed_validation",
            "finished_at": iso_now(),
        },
    )
