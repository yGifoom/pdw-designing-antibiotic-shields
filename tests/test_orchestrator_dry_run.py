import argparse
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.orchestrator import run


class OrchestratorDryRunTests(unittest.TestCase):
    def test_dry_run_does_not_create_scratch_dirs(self) -> None:
        cfg_text = """
run_id: dryrun-no-mkdir
preset: fast
scratch_root: /mnt/scratch/should-not-be-created
target_input: /mnt/shared-ro/targets/t.pdb
cluster:
  project: p
  namespace: n
  scratch_pvc: s
  shared_ro_pvc: ro
images:
  rfd3: img1
  ligandmpnn: img2
  af3: img3
stage_overrides:
  03_rfd3_backbones:
    params:
      rfd3_input_jsons: ["./tests/data/rfd3_a.json"]
"""
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "cfg.yaml"
            cfg_path.write_text(cfg_text)

            args = argparse.Namespace(config=str(cfg_path), dry_run=True)
            with patch("pipeline.orchestrator.Path.mkdir", side_effect=AssertionError("mkdir should not be called in dry-run")):
                with patch("pipeline.orchestrator.submit_or_echo", return_value=0):
                    rc = run(args)
            self.assertEqual(rc, 0)

    def test_submit_mode_without_local_state_does_not_mkdir(self) -> None:
        cfg_text = """
run_id: submit-no-local-state
preset: fast
scratch_root: /mnt/scratch/should-not-be-created
target_input: /mnt/shared-ro/targets/t.pdb
cluster:
  project: p
  namespace: n
  scratch_pvc: s
  shared_ro_pvc: ro
images:
  rfd3: img1
  ligandmpnn: img2
  af3: img3
stage_overrides:
  03_rfd3_backbones:
    params:
      rfd3_input_jsons: ["./tests/data/rfd3_a.json"]
"""
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "cfg.yaml"
            cfg_path.write_text(cfg_text)

            args = argparse.Namespace(config=str(cfg_path), dry_run=False)
            with patch("pipeline.orchestrator.Path.mkdir", side_effect=AssertionError("mkdir should not be called with PIPELINE_LOCAL_STATE=0")):
                with patch("pipeline.orchestrator.submit_or_echo", return_value=0):
                    rc = run(args)
            self.assertEqual(rc, 0)

    def test_env_overrides_cluster_pvcs_for_direct_orchestrator_run(self) -> None:
        cfg_text = """
run_id: override-cluster
preset: fast
scratch_root: /mnt/scratch/should-not-be-created
target_input: /mnt/shared-ro/targets/t.pdb
cluster:
  project: from-config
  namespace: from-config-ns
  scratch_pvc: from-config-scratch
  shared_ro_pvc: from-config-shared
images:
  rfd3: img1
  ligandmpnn: img2
  af3: img3
stage_overrides:
  03_rfd3_backbones:
    params:
      rfd3_input_jsons: ["./tests/data/rfd3_a.json"]
"""
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "cfg.yaml"
            cfg_path.write_text(cfg_text)
            args = argparse.Namespace(config=str(cfg_path), dry_run=True)

            captured = []

            def _capture(spec, dry_run=False):  # type: ignore[no-untyped-def]
                captured.append(spec)
                return 0

            with patch.dict(
                os.environ,
                {
                    "RUNAI_PROJECT": "hackathon-proteindesign-testuser",
                    "RUNAI_NAMESPACE": "protein-design",
                    "SCRATCH_PVC": "hackathon-proteindesign-scratch-g04",
                    "SHARED_RO_PVC": "hackathon-proteindesign-shared-ro",
                },
                clear=False,
            ):
                with patch("pipeline.orchestrator.submit_or_echo", side_effect=_capture):
                    rc = run(args)
            self.assertEqual(rc, 0)
            self.assertTrue(captured)
            self.assertEqual(captured[0].cluster.project, "hackathon-proteindesign-testuser")
            self.assertEqual(captured[0].cluster.scratch_pvc, "hackathon-proteindesign-scratch-g04")
            self.assertEqual(captured[0].cluster.shared_ro_pvc, "hackathon-proteindesign-shared-ro")


if __name__ == "__main__":
    unittest.main()
