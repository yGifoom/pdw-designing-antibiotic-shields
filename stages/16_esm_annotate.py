from __future__ import annotations

from pipeline.diagnostics import write_csv, write_json
from pipeline.types import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    # TODO(tool-integration): integrate external tool commands for 16_esm_annotate.
    write_csv(ctx.stage_dir / "summary.csv", [{"stage": "16_esm_annotate", "note": "placeholder implementation"}])
    write_json(ctx.stage_dir / "metrics.json", {"stage": "16_esm_annotate", "status": "placeholder"})
    return StageResult(stage_key=ctx.stage_spec.key, success=True)
