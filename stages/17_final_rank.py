from __future__ import annotations

import csv
import json
from pipeline.diagnostics import write_csv, write_json
from pipeline.types import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    af3 = {}
    sanity = {}
    for path, sink, key in [
        (ctx.run_root / "14_af3_rescore" / "summary.csv", af3, "candidate_id"),
        (ctx.run_root / "15_bioemu_candidate_sanity" / "summary.csv", sanity, "candidate_id"),
    ]:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    sink[row[key]] = row

    weights = ctx.config.get("ranking", {}).get("final_weights", {})
    rows = []
    lineage = []
    for cid, a in af3.items():
        s = sanity.get(cid, {})
        ptm = float(a.get("pTM", 0))
        iptm = float(a.get("ipTM", 0))
        ipsae = float(a.get("ipSAE", 0))
        pose = float(a.get("pose_retention", 0))
        geom = float(a.get("interface_geometry", 0))
        fold = float(s.get("fold_occupancy", 0))
        helix = float(s.get("helix_occupancy", 0))
        sheet = float(s.get("sheet_occupancy", 0))
        comp = float(s.get("radius_compactness", 0))
        basins = float(s.get("competing_fold_basins", 99))
        score = (
            ptm * weights.get("pTM", 1)
            + iptm * weights.get("ipTM", 1)
            + ipsae * weights.get("ipSAE", 1.2)
            + pose * weights.get("pose_retention", 1)
            + geom * weights.get("interface_geometry", 1)
            + fold * weights.get("fold_occupancy", 1)
            + helix * weights.get("helix_occupancy", 0.5)
            + sheet * weights.get("sheet_occupancy", 0.5)
            + comp * weights.get("radius_compactness", 0.3)
            - basins * weights.get("competing_fold_basins_penalty", 0.2)
        )
        rows.append({"candidate_id": cid, "final_score": round(score, 4), "pTM": ptm, "ipTM": iptm, "ipSAE": ipsae, "fold_occupancy": fold, "helix_occupancy": helix, "sheet_occupancy": sheet, "radius_compactness": comp, "competing_fold_basins": basins})

    rows.sort(key=lambda x: x["final_score"], reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["final_rank"] = rank
        lineage.append({"candidate_id": row["candidate_id"], "run_id": ctx.run_id, "final_rank": rank, "pTM": row["pTM"], "ipTM": row["ipTM"], "ipSAE": row["ipSAE"], "fold_occupancy": row["fold_occupancy"], "helix_occupancy": row["helix_occupancy"], "sheet_occupancy": row["sheet_occupancy"], "radius_compactness": row["radius_compactness"], "competing_fold_basins": row["competing_fold_basins"]})

    write_csv(ctx.stage_dir / "summary.csv", rows)
    write_json(ctx.stage_dir / "metrics.json", {"ranked_candidates": len(rows), "weights": weights})
    (ctx.stage_dir / "lineage_updates.json").write_text(json.dumps(lineage, indent=2), encoding="utf-8")
    return StageResult(stage_key=ctx.stage_spec.key, success=True, outputs=["lineage_updates.json"])