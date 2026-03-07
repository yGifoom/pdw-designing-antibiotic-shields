from __future__ import annotations

from pipeline.diagnostics import write_csv, write_json
from pipeline.types import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    report = """# Lane 2 Run Report

This report aggregates stage metrics, filtering rationale, and final candidate summaries.

- TODO(tool-integration): render richer plots and HTML dashboard.
"""
    (ctx.stage_dir / "report.md").write_text(report, encoding="utf-8")
    write_csv(ctx.stage_dir / "summary.csv", [{"section": "overview", "status": "generated"}])
    write_json(ctx.stage_dir / "metrics.json", {"report_generated": True})
    return StageResult(stage_key=ctx.stage_spec.key, success=True, outputs=["report.md"])