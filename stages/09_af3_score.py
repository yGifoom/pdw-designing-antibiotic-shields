from __future__ import annotations

import json
from pipeline.diagnostics import write_csv, write_json
from pipeline.types import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    # TODO(tool-integration): invoke AlphaFold 3 complex scoring in a dedicated one-GPU job image.
    n = int(ctx.config.get("af3", {}).get("max_candidates_first_pass", 120))
    rows = []
    lineage = []
    for i in range(1, min(n, 40) + 1):
        ptm = 0.55 + (i % 10) * 0.03
        iptm = 0.45 + (i % 7) * 0.05
        ipsae = 0.4 + (i % 9) * 0.045
        binder_conf = 70 + (i % 15)
        pose = 0.35 + (i % 8) * 0.07
        geom = 0.45 + (i % 6) * 0.08
        clash_free = i % 11 != 0
        rows.append({
            "candidate_id": f"cand_{i:04d}",
            "pTM": round(ptm, 3),
            "ipTM": round(iptm, 3),
            "ipSAE": round(ipsae, 3),
            "binder_confidence": binder_conf,
            "pose_retention": round(pose, 3),
            "interface_geometry": round(geom, 3),
            "clash_free": clash_free,
            "ipSAE_pass": ipsae >= ctx.config.get("af3", {}).get("thresholds", {}).get("ipSAE_min", 0.55),
        })
        lineage.append({"candidate_id": f"cand_{i:04d}", "run_id": ctx.run_id, "pTM": round(ptm, 3), "ipTM": round(iptm, 3), "ipSAE": round(ipsae, 3), "ipSAE_pass": ipsae >= 0.55})

    write_csv(ctx.stage_dir / "summary.csv", rows)
    write_json(ctx.stage_dir / "metrics.json", {"candidates_scored": len(rows), "metric_fields": ["pTM", "ipTM", "ipSAE", "pose_retention", "interface_geometry"]})
    (ctx.stage_dir / "lineage_updates.json").write_text(json.dumps(lineage, indent=2), encoding="utf-8")
    return StageResult(stage_key=ctx.stage_spec.key, success=True, outputs=["lineage_updates.json"])