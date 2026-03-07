from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from pipeline.config import ClusterConfig, StageConfig


@dataclass(slots=True)
class RunaiJobSpec:
    name: str
    image: str
    command: str
    stage_cfg: StageConfig
    cluster: ClusterConfig
    run_root: Path


def build_submit_command(spec: RunaiJobSpec) -> list[str]:
    cmd = [
        "runai",
        "submit",
        "--name",
        spec.name,
        "--project",
        spec.cluster.project,
        "--image",
        spec.image,
        "--gpu",
        str(spec.stage_cfg.gpu),
        "--cpu",
        str(spec.stage_cfg.cpu),
        "--memory",
        spec.stage_cfg.memory,
        "--pvc",
        f"{spec.cluster.scratch_pvc}:{spec.cluster.scratch_mount}",
        "--pvc",
        f"{spec.cluster.shared_ro_pvc}:{spec.cluster.shared_ro_mount}:ro",
        "--backoff-limit",
        "0",
        "--command",
        "--",
        "bash",
        "-lc",
        spec.command,
    ]

    # Compatibility toggle for newer RunAI CLIs that support active deadline.
    if os.environ.get("RUNAI_ENABLE_ACTIVE_DEADLINE", "0") == "1":
        cmd[cmd.index("--command"):cmd.index("--command")] = [
            "--active-deadline-seconds",
            str(spec.stage_cfg.timeout_minutes * 60),
        ]
    return cmd


def submit_or_echo(spec: RunaiJobSpec, dry_run: bool = False) -> int:
    cmd = build_submit_command(spec)
    print(
        f"[runai] submit name={spec.name} project={spec.cluster.project} "
        f"image={spec.image} gpu={spec.stage_cfg.gpu} cpu={spec.stage_cfg.cpu} mem={spec.stage_cfg.memory}"
    )
    if os.environ.get("PIPELINE_VERBOSE_COMMANDS", "0") == "1":
        rendered = " ".join(shlex.quote(part) for part in cmd)
        print(f"[runai][cmd] {rendered}")
    if dry_run:
        return 0
    proc = subprocess.run(cmd, check=False)
    return proc.returncode
