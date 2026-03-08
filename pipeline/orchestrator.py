from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
from pathlib import Path
from typing import Dict

from pipeline.config import load_config
from pipeline.runai import RunaiJobSpec, submit_or_echo, wait_for_job
from pipeline.stage_contract import StageContext, ensure_stage_dir, stage_completed, write_json
from pipeline.stage_commands import build_stage_script
from pipeline.stages import STAGES, resolve_stage_config
from pathlib import PurePosixPath


def _resolve_container_scratch_root(host_scratch_root: Path, scratch_mount: str) -> Path:
    override = os.environ.get("CONTAINER_SCRATCH_ROOT")
    if override:
        return Path(override)

    mount = Path(scratch_mount)
    try:
        host_scratch_root.relative_to(mount)
        return host_scratch_root
    except ValueError:
        # If host path is not container-visible (e.g. /mnt/hackathon-.../scratch-gXX/pdw-lane1),
        # map to mounted container scratch using the leaf run folder name.
        return mount / host_scratch_root.name


def run(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config))
    # Allow shell env overrides so users can run either the launcher script or
    # `python -m pipeline.orchestrator --config ...` directly with the same exports.
    if os.environ.get("RUNAI_PROJECT"):
        cfg.cluster.project = os.environ["RUNAI_PROJECT"]
    if os.environ.get("RUNAI_NAMESPACE"):
        cfg.cluster.namespace = os.environ["RUNAI_NAMESPACE"]
    if os.environ.get("SCRATCH_PVC"):
        cfg.cluster.scratch_pvc = os.environ["SCRATCH_PVC"]
    if os.environ.get("SHARED_RO_PVC"):
        cfg.cluster.shared_ro_pvc = os.environ["SHARED_RO_PVC"]

    run_root = cfg.scratch_root / cfg.run_id
    container_scratch_root = _resolve_container_scratch_root(cfg.scratch_root, cfg.cluster.scratch_mount)
    container_run_root = PurePosixPath((container_scratch_root / cfg.run_id).as_posix())
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

    if not args.dry_run and not local_state_enabled and run_root != container_run_root:
        print(
            f"[orchestrator] host scratch_root={run_root} -> container scratch_root={container_run_root} "
            "(override with CONTAINER_SCRATCH_ROOT if needed)"
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
            f"export TARGET_INPUT={shlex.quote(cfg.target_input.as_posix())}; "
            f"export RFD3_INPUT_JSON_LIST={shlex.quote(','.join(rfd3_json_list))}; "
            f"export RFD3_INPUT_JSON_GLOB={shlex.quote(rfd3_json_glob)}; "
            f"export AF3_FASTA_GLOB={shlex.quote((container_run_root / '04_ligandmpnn_design' / 'output' / '*' / 'seqs' / '*.fa').as_posix())}; "
            f"export THRESHOLD_PTM={shlex.quote(str(cfg.thresholds.pTM_min))}; "
            f"export THRESHOLD_IPTM={shlex.quote(str(cfg.thresholds.ipTM_min))}; "
            f"export THRESHOLD_IPSAE={shlex.quote(str(cfg.thresholds.ipSAE_min))}; "
            f"export THRESHOLD_PLDDT={shlex.quote(str(cfg.thresholds.pLDDT_min))}; "
            f"export THRESHOLD_IPAE={shlex.quote(str(cfg.thresholds.iPAE_max))}; "
            f"export THRESHOLD_RMSD={shlex.quote(str(cfg.thresholds.rmsd_max))}; "
            f"export WEIGHT_PTM={shlex.quote(str(cfg.ranking_weights.pTM))}; "
            f"export WEIGHT_IPTM={shlex.quote(str(cfg.ranking_weights.ipTM))}; "
            f"export WEIGHT_IPSAE={shlex.quote(str(cfg.ranking_weights.ipSAE))}; "
            f"export WEIGHT_PLDDT={shlex.quote(str(cfg.ranking_weights.pLDDT))}; "
            f"export WEIGHT_IPAE_PENALTY={shlex.quote(str(cfg.ranking_weights.iPAE_penalty))}; "
            f"export WEIGHT_RMSD_PENALTY={shlex.quote(str(cfg.ranking_weights.rmsd_penalty))}; "
        )
        cmd = env_prefix + build_stage_script(container_run_root, stage.name)
        job_spec = RunaiJobSpec(
            name=f"{cfg.run_id}-{stage.name}".replace("_", "-")[:63],
            image=stage_cfg.image or cfg.images.orchestrator,
            command=cmd,
            stage_cfg=stage_cfg,
            cluster=cfg.cluster,
            run_root=container_run_root,
        )

        rc = submit_or_echo(job_spec, dry_run=args.dry_run)
        if args.dry_run:
            stage_states[stage.name] = "completed"
        elif rc != 0:
            stage_states[stage.name] = f"submit_failed:{rc}"
        else:
            # Wait for the container job to actually finish before proceeding
            # to the next stage — runai submit only confirms acceptance.
            final_state = wait_for_job(
                job_spec.name, job_spec.cluster, stage_cfg.timeout_minutes
            )
            stage_states[stage.name] = final_state

    if not args.dry_run and local_state_enabled:
        write_json(run_root / "orchestrator_state.json", stage_states)
    print(json.dumps(stage_states, indent=2))
    return 0


def main() -> int:
    # Avoid noisy BrokenPipeError tracebacks when piping output (e.g. `| head`).
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Lane-1 binder design orchestrator")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Print runai commands only")
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
