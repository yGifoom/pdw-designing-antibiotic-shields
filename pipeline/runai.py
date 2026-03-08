from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from pipeline.config import ClusterConfig, StageConfig


def _safe_print(msg: str) -> None:
    try:
        print(msg)
    except BrokenPipeError:
        # Support piping orchestrator output to tools like `head`.
        return


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
    _safe_print(
        f"[runai] submit name={spec.name} project={spec.cluster.project} "
        f"image={spec.image} gpu={spec.stage_cfg.gpu} cpu={spec.stage_cfg.cpu} mem={spec.stage_cfg.memory}"
    )
    if os.environ.get("PIPELINE_VERBOSE_COMMANDS", "0") == "1":
        rendered = " ".join(shlex.quote(part) for part in cmd)
        _safe_print(f"[runai][cmd] {rendered}")
    if dry_run:
        return 0
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


def wait_for_job(
    job_name: str,
    cluster: ClusterConfig,
    timeout_minutes: int = 240,
    poll_interval: int = 30,
) -> str:
    """Poll ``runai describe job`` until the job reaches a terminal state.

    Returns one of:
      - ``"completed"``   – job succeeded
      - ``"failed:<name>"`` – job failed or errored
      - ``"timeout:<name>"`` – deadline exceeded without terminal state
    """
    import time

    deadline = time.time() + timeout_minutes * 60
    _safe_print(
        f"[runai][wait] waiting for job {job_name} "
        f"(timeout {timeout_minutes}m, poll every {poll_interval}s)"
    )
    while time.time() < deadline:
        proc = subprocess.run(
            ["runai", "describe", "job", job_name, "--project", cluster.project],
            capture_output=True,
            text=True,
            check=False,
        )
        stdout_lower = proc.stdout.lower()
        # RunAI describe output contains a "Status:" line with the job state.
        if "succeeded" in stdout_lower:
            _safe_print(f"[runai][wait] {job_name} succeeded")
            return "completed"
        if "failed" in stdout_lower or "error" in stdout_lower:
            _safe_print(f"[runai][wait] {job_name} failed/errored")
            return f"failed:{job_name}"

        _safe_print(
            f"[runai][wait] {job_name} still running... "
            f"(next check in {poll_interval}s)"
        )
        time.sleep(poll_interval)

    _safe_print(f"[runai][wait] {job_name} timed out after {timeout_minutes}m")
    return f"timeout:{job_name}"
