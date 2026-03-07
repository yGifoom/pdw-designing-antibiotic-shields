import unittest
from pathlib import Path

from pipeline.stage_commands import build_stage_script


class StageCommandTests(unittest.TestCase):
    def test_rfd3_stage_supports_multiple_input_sources(self) -> None:
        script = build_stage_script(Path('/tmp/run'), '03_rfd3_backbones')
        self.assertIn('RFD3_INPUT_JSON_LIST', script)
        self.assertIn('RFD3_INPUT_JSON_GLOB', script)
        self.assertIn("params.get('rfd3_input_jsons'", script)
        self.assertIn("params.get('rfd3_input_glob'", script)
        self.assertIn("while IFS= read -r INPUT_JSON", script)

    def test_ligandmpnn_stage_supports_checkpoint_override(self) -> None:
        script = build_stage_script(Path('/tmp/run'), '04_ligandmpnn_design')
        self.assertIn('LIGANDMPNN_CHECKPOINT', script)


if __name__ == '__main__':
    unittest.main()
