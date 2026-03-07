from __future__ import annotations

from pipeline.diagnostics import write_csv, write_json
from pipeline.hotspot_schema import DEFAULT_KEEP_RULES, merge_sources
from pipeline.types import StageContext, StageResult


def run(ctx: StageContext) -> StageResult:
    hotspot_cfg = ctx.config.get("hotspot", {})
    mode = hotspot_cfg.get("mode", "auto")
    weights = hotspot_cfg.get("weights", {})
    reps = [f"rep_{i:03d}" for i in range(1, int(ctx.config.get("bioemu", {}).get("representatives", 10)) + 1)]

    # TODO(tool-integration): pocket detection, PeSTo scoring, conservation mapping, catalytic priors.
    patches = []
    for i, rep in enumerate(reps, start=1):
        pocket = 0.4 + (i % 5) * 0.1
        pesto = 0.3 + (i % 7) * 0.07
        conservation = 0.2 + (i % 3) * 0.12
        catalytic = 0.1 + (i % 4) * 0.1
        ligand = 0.2 + (i % 2) * 0.2
        exposure = 0.3 + (i % 6) * 0.09
        total = (
            pocket * weights.get("pocket", 1.0)
            + pesto * weights.get("pesto", 1.0)
            + conservation * weights.get("conservation", 0.8)
            + catalytic * weights.get("catalytic_prior", 0.6)
            + ligand * weights.get("ligand_context", 0.7)
            + exposure * weights.get("exposure_persistence", 1.0)
        )
        patches.append(
            {
                "hotspot_id": f"auto_hs_{i:03d}",
                "conformer_id": rep,
                "source": "auto",
                "pocket_score": round(pocket, 3),
                "pesto_score": round(pesto, 3),
                "conservation_score": round(conservation, 3),
                "catalytic_prior_score": round(catalytic, 3),
                "ligand_context_score": round(ligand, 3),
                "exposure_persistence_score": round(exposure, 3),
                "total_score": round(total, 3),
                "patch_size": 4 + i % 8,
                "keep": total >= DEFAULT_KEEP_RULES["min_total_score"],
                "keep_drop_rationale": "passed weighted threshold"
                if total >= DEFAULT_KEEP_RULES["min_total_score"]
                else "below threshold",
            }
        )

    manual = hotspot_cfg.get("manual_hotspots", []) if mode in {"manual", "hybrid"} else []
    manual_ids = [entry.get("hotspot_id", f"manual_hs_{i:03d}") for i, entry in enumerate(manual, start=1)]
    auto_ids = [p["hotspot_id"] for p in patches]
    merged = merge_sources(manual_ids, auto_ids) if mode == "hybrid" else []

    write_csv(ctx.stage_dir / "summary.csv", patches)
    write_json(
        ctx.stage_dir / "metrics.json",
        {
            "mode": mode,
            "representatives_processed": len(reps),
            "auto_hotspots": len(auto_ids),
            "manual_hotspots": len(manual_ids),
            "merged_hotspots": len(merged),
            "weights": weights,
            "keep_rules": DEFAULT_KEEP_RULES,
        },
    )
    write_json(ctx.stage_dir / "hotspot_sources.json", {"merged": merged, "mode": mode})
    (ctx.stage_dir / "representative_conformers.txt").write_text("\n".join(reps), encoding="utf-8")
    (ctx.stage_dir / "pocket_summaries.txt").write_text(
        "TODO(tool-integration): write pocket detector outputs", encoding="utf-8"
    )
    (ctx.stage_dir / "per_residue_pesto_scores.tsv").write_text("TODO(tool-integration)\n", encoding="utf-8")
    return StageResult(
        stage_key=ctx.stage_spec.key,
        success=True,
        outputs=["hotspot_sources.json", "representative_conformers.txt", "pocket_summaries.txt", "per_residue_pesto_scores.tsv"],
    )
