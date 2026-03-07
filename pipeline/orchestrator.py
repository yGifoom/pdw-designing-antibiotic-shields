from __future__ import annotations

import argparse
import json
import os
import shlex
from pathlib import Path
from typing import Dict

from pipeline.config import load_config
from pipeline.runai import RunaiJobSpec, submit_or_echo
from pipeline.stage_contract import StageContext, ensure_stage_dir, stage_completed, write_json
from pipeline.stage_commands import build_stage_script
from pipeline.stages import STAGES, resolve_stage_config


def run(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config))
    run_root = cfg.scratch_root / cfg.run_id
    local_state_enabled = os.environ.get("PIPELINE_LOCAL_STATE", "0") == "1"

    if not args.dry_run and local_state_enabled:
        try:
            run_root.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise PermissionError(
                "Cannot create scratch run root. If launching from SSH/login host, "
                "set `scratch_root` to your host-visible scratch path (e.g. "
                "`/mnt/hackathon-proteindesign/.../scratch-gXX/...`) and reserve "
                "`/mnt/scratch` for in-container paths."
            ) from exc

        write_json(
            run_root / "run_manifest.json",
            {
                "run_id": cfg.run_id,
                "preset": cfg.preset,
                "target_input": str(cfg.target_input),
                "hotspots_file": str(cfg.hotspots_file) if cfg.hotspots_file else None,
                "hotspot_count": None,
            },
        )

    stage_states: Dict[str, str] = {}

    for stage in STAGES:
        stage_cfg = resolve_stage_config(cfg, stage)
        stage_dir = run_root / stage.name

        if not stage_cfg.enabled:
            stage_states[stage.name] = "disabled"
            continue

        blocked = [dep for dep in stage.dependencies if stage_states.get(dep) not in {"completed", "skipped", "disabled"}]
        if blocked:
            stage_states[stage.name] = f"blocked_by:{','.join(blocked)}"
            continue

        try:
            already_done = stage_completed(stage_dir) if local_state_enabled else False
        except OSError:
            already_done = False

        if already_done:
            print(f"[skip] {stage.name} already completed")
            stage_states[stage.name] = "skipped"
            continue

        if not args.dry_run and local_state_enabled:
            ensure_stage_dir(StageContext(cfg.run_id, stage.name, run_root))
            write_json(stage_dir / "params.json", stage_cfg.params)
            write_json(
                stage_dir / "provenance.json",
                {
                    "stage": stage.name,
                    "image": stage_cfg.image,
                    "dependencies": stage.dependencies,
                    "preset": cfg.preset,
                },
            )

        rfd3_params = cfg.stage_overrides.get("03_rfd3_backbones")
        rfd3_json_list = []
        rfd3_json_glob = ""
        if rfd3_params:
            rfd3_json_list = [str(x) for x in (rfd3_params.params.get("rfd3_input_jsons", []) or [])]
            rfd3_json_glob = str(rfd3_params.params.get("rfd3_input_glob", ""))

        env_prefix = (
            f"export TARGET_INPUT={shlex.quote(str(cfg.target_input))}; "
            f"export RFD3_INPUT_JSON_LIST={shlex.quote(','.join(rfd3_json_list))}; "
            f"export RFD3_INPUT_JSON_GLOB={shlex.quote(rfd3_json_glob)}; "
            f"export AF3_FASTA_GLOB={shlex.quote(str(run_root / '04_ligandmpnn_design' / 'output' / '*' / 'seqs' / '*.fa'))}; "
        )
        cmd = env_prefix + build_stage_script(run_root, stage.name)
        job_spec = RunaiJobSpec(
            name=f"{cfg.run_id}-{stage.name}".replace("_", "-")[:63],
            image=stage_cfg.image or cfg.images.orchestrator,
            command=cmd,
            stage_cfg=stage_cfg,
            cluster=cfg.cluster,
            run_root=run_root,
        )

        rc = submit_or_echo(job_spec, dry_run=args.dry_run)
        stage_states[stage.name] = "completed" if (args.dry_run or rc == 0) else f"submit_failed:{rc}"

    if not args.dry_run and local_state_enabled:
        write_json(run_root / "orchestrator_state.json", stage_states)
    print(json.dumps(stage_states, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Lane-1 binder design orchestrator")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Print runai commands only")
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
