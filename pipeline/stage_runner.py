from __future__ import annotations

import importlib
from pathlib import Path
from typing import Dict, List

from pipeline.diagnostics import initialize_stage_logs, utc_now, write_csv, write_json
from pipeline.types import StageContext, StageResult, StageSpec
from pipeline.validation import validate_stage_directory


def _read_status(stage_dir: Path) -> Dict[str, object]:
    status = stage_dir / "status.json"
    if not status.exists():
        return {}
    import json

    return json.loads(status.read_text(encoding="utf-8"))


def stage_completed(stage_dir: Path) -> bool:
    status = _read_status(stage_dir)
    if status.get("state") != "completed":
        return False
    validation = stage_dir / "validation.json"
    if not validation.exists():
        return False
    import json

    v = json.loads(validation.read_text(encoding="utf-8"))
    return bool(v.get("valid"))


def run_stage(spec: StageSpec, run_root: Path, run_id: str, config: Dict[str, object], dry_run: bool) -> StageResult:
    stage_dir = run_root / spec.key
    stage_dir.mkdir(parents=True, exist_ok=True)

    if stage_completed(stage_dir):
        return StageResult(stage_key=spec.key, success=True, skipped=True, message="Already completed")

    initialize_stage_logs(stage_dir)
    write_json(stage_dir / "status.json", {"state": "running", "stage": spec.key, "started_at": utc_now()})
    write_json(stage_dir / "params.json", config.get(spec.key, {}))
    write_json(
        stage_dir / "provenance.json",
        {
            "stage": spec.key,
            "module": spec.module,
            "image": spec.image,
            "resources": spec.resources.__dict__,
            "run_id": run_id,
            "todo": "TODO(tool-integration): replace placeholders with real model invocations",
        },
    )

    if dry_run:
        write_json(stage_dir / "metrics.json", {"dry_run": True, "stage": spec.key})
        write_csv(stage_dir / "summary.csv", [{"stage": spec.key, "dry_run": True}])
        v = validate_stage_directory(stage_dir)
        write_json(stage_dir / "status.json", {"state": "completed", "stage": spec.key, "completed_at": utc_now(), "dry_run": True})
        return StageResult(stage_key=spec.key, success=bool(v["valid"]), message="Dry run", skipped=False)

    module = importlib.import_module(spec.module)
    ctx = StageContext(
        run_id=run_id,
        scratch_root=run_root.parent,
        run_root=run_root,
        stage_dir=stage_dir,
        config=config,
        stage_spec=spec,
    )
    stage_func = getattr(module, "run")
    result: StageResult = stage_func(ctx)
    v = validate_stage_directory(stage_dir, result.outputs)
    final_state = "completed" if result.success and v["valid"] else "failed"
    write_json(
        stage_dir / "status.json",
        {
            "state": final_state,
            "stage": spec.key,
            "completed_at": utc_now(),
            "message": result.message,
            "skipped": result.skipped,
        },
    )
    result.success = bool(result.success and v["valid"])
    return result
