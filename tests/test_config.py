from pathlib import Path

from pipeline.config import load_config


def test_load_minimal_fast_config() -> None:
    cfg = load_config(Path("configs/minimal_fast.yaml"))
    assert cfg["preset"] == "fast"
    assert cfg["hotspot"]["mode"] in {"manual", "auto", "hybrid"}


def test_gpu_constraint() -> None:
    cfg = load_config(Path("configs/minimal_fast.yaml"))
    for stage in cfg["stages"].values():
        assert stage["resources"]["gpu"] in [0, 1]
