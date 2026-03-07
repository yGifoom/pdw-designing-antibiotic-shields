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


if __name__ == "__main__":
    unittest.main()
