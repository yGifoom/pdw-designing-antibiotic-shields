from __future__ import annotations

from pathlib import Path

from pipeline.types import StageSpec


def render_slurm_script(stage: StageSpec, command: str, log_dir: Path) -> str:
    gpu_line = f"#SBATCH --gpus={stage.resources.gpu}" if stage.resources.gpu else ""
    return f"""#!/bin/bash
#SBATCH --job-name={stage.key}
#SBATCH --cpus-per-task={stage.resources.cpu}
#SBATCH --mem={stage.resources.memory_gb}G
#SBATCH --time=0-{stage.resources.walltime_min}
{gpu_line}
#SBATCH --output={log_dir / 'stdout.log'}
#SBATCH --error={log_dir / 'stderr.log'}

# TODO(tool-integration): stage-specific image launch should be wired here.
{command}
"""
