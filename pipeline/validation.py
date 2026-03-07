from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

from pipeline.diagnostics import write_json


REQUIRED_STAGE_FILES = [
    "status.json",
    "params.json",
    "metrics.json",
    "provenance.json",
    "summary.csv",
    "validation.json",
    "stdout.log",
    "stderr.log",
]


def validate_stage_directory(stage_dir: Path, extra_outputs: Iterable[str] | None = None) -> Dict[str, object]:
    expected = list(REQUIRED_STAGE_FILES)
    if extra_outputs:
        expected.extend(extra_outputs)
    missing = [name for name in expected if not (stage_dir / name).exists()]
    payload = {
        "valid": not missing,
        "missing": missing,
        "expected": expected,
    }
    write_json(stage_dir / "validation.json", payload)
    return payload
