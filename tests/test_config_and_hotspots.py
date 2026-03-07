import tempfile
import unittest
from pathlib import Path

from pipeline.config import load_config
from pipeline.hotspots import load_hotspots


class ConfigHotspotTests(unittest.TestCase):
    def test_load_fast_config(self) -> None:
        cfg = load_config(Path("configs/lane1.fast.yaml"))
        self.assertEqual(cfg.preset, "fast")
        self.assertEqual(cfg.images.af3, "registry.rcp.epfl.ch/proteindesign-containers/af3:2026.1")

    def test_hotspots_modes(self) -> None:
        records = load_hotspots(Path("examples/hotspots.manual.yaml"))
        self.assertEqual(len(records), 4)
        self.assertIn(records[0].mode, {"residue_list", "residue_range", "center_radius", "chain_residues"})

    def test_config_without_hotspots_file_is_allowed(self) -> None:
        cfg_text = """
run_id: r1
preset: fast
scratch_root: /mnt/scratch/x
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
"""
        p = Path('tests/.tmp_cfg.yaml')
        p.write_text(cfg_text)
        try:
            cfg = load_config(p)
            self.assertIsNone(cfg.hotspots_file)
        finally:
            p.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
