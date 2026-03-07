from __future__ import annotations

import csv
import json
from pipeline.diagnostics import write_csv, write_json
from pipeline.types import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    af3_path = ctx.run_root / "09_af3_score" / "summary.csv"
    thresholds = ctx.config.get("af3", {}).get("thresholds", {})
    weights = ctx.config.get("ranking", {}).get("first_pass_weights", {})
    rows = []
    if af3_path.exists():
        with af3_path.open("r", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    kept = []
    for row in rows:
        ptm = float(row.get("pTM", 0))
        iptm = float(row.get("ipTM", 0))
        ipsae = float(row.get("ipSAE", 0))
        pose = float(row.get("pose_retention", 0))
        geom = float(row.get("interface_geometry", 0))
        clash_free = row.get("clash_free", "False") == "True"
        passes = (
            ptm >= thresholds.get("pTM_min", 0)
            and iptm >= thresholds.get("ipTM_min", 0)
            and ipsae >= thresholds.get("ipSAE_min", 0)
            and clash_free
        )
        comp = (
            ptm * weights.get("pTM", 1.0)
            + iptm * weights.get("ipTM", 1.0)
            + ipsae * weights.get("ipSAE", 1.2)
            + pose * weights.get("pose_retention", 1.0)
            + geom * weights.get("interface_geometry", 1.0)
        )
        row["first_pass_pass"] = passes
        row["first_pass_score"] = round(comp, 4)
        row["filter_reason"] = "pass" if passes else "failed threshold/clash"
        kept.append(row)
    kept.sort(key=lambda r: float(r.get("first_pass_score", 0)), reverse=True)
    for rank, row in enumerate(kept, start=1):
        row["first_pass_rank"] = rank

    write_csv(ctx.stage_dir / "summary.csv", kept)
    write_json(ctx.stage_dir / "metrics.json", {"evaluated": len(rows), "kept": sum(1 for r in kept if str(r["first_pass_pass"]) == "True"), "thresholds": thresholds, "weights": weights})
    (ctx.stage_dir / "lineage_updates.json").write_text(json.dumps([{"candidate_id": r.get("candidate_id"), "first_pass_parent": r.get("candidate_id")} for r in kept if str(r.get("first_pass_pass")) == "True"], indent=2), encoding="utf-8")
    return StageResult(stage_key=ctx.stage_spec.key, success=True, outputs=["lineage_updates.json"])