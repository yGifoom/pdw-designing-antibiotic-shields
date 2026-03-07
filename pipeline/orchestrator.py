from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from pipeline.config import load_config, snapshot_config
from pipeline.diagnostics import write_csv, write_json
from pipeline.lineage import write_lineage
from pipeline.stage_registry import STAGE_ORDER, build_stage_specs, select_stage_window
from pipeline.stage_runner import run_stage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lane 2 dynamics-aware pipeline orchestrator")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--run-id", type=str, required=True)
    parser.add_argument("--start-stage", type=str)
    parser.add_argument("--end-stage", type=str)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _build_stage_index(specs) -> List[Dict[str, object]]:
    return [
        {
            "order": s.order,
            "stage": s.key,
            "enabled": s.enabled,
            "image": s.image,
            "cpu": s.resources.cpu,
            "memory_gb": s.resources.memory_gb,
            "gpu": s.resources.gpu,
        }
        for s in specs
    ]


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    run_root = args.scratch_root / args.run_id
    run_root.mkdir(parents=True, exist_ok=True)

    snapshot_config(config, run_root)

    specs = [s for s in build_stage_specs(config) if s.enabled]
    enabled_keys = [s.key for s in specs]
    target_keys = set(select_stage_window(enabled_keys, args.start_stage, args.end_stage))

    write_csv(run_root / "stage_index.csv", _build_stage_index(specs))

    run_manifest = {
        "run_id": args.run_id,
        "scratch_root": str(args.scratch_root),
        "run_root": str(run_root),
        "start_stage": args.start_stage,
        "end_stage": args.end_stage,
        "dry_run": args.dry_run,
    }
    write_json(run_root / "run_manifest.json", run_manifest)

    stage_results: List[Dict[str, object]] = []
    lineage_rows: List[Dict[str, object]] = []

    for spec in specs:
        if spec.key not in target_keys:
            continue
        result = run_stage(spec, run_root=run_root, run_id=args.run_id, config=config, dry_run=args.dry_run)
        stage_results.append(
            {
                "stage": spec.key,
                "success": result.success,
                "skipped": result.skipped,
                "message": result.message,
            }
        )
        if not result.success:
            break

        lineage_path = run_root / spec.key / "lineage_updates.json"
        if lineage_path.exists():
            lineage_rows.extend(json.loads(lineage_path.read_text(encoding="utf-8")))

    write_csv(run_root / "orchestrator_stage_results.csv", stage_results)
    write_lineage(run_root / "candidate_lineage.csv", lineage_rows)


if __name__ == "__main__":
    main()
