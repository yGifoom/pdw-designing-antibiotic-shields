import json
import tempfile
import unittest
from pathlib import Path

from pipeline.stage_contract import MANDATORY_STAGE_FILES, StageContext, finalize_stage, initialize_stage, stage_completed


class StageContractTests(unittest.TestCase):
    def test_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ctx = StageContext(run_id="r1", stage_name="s1", run_root=root)
            initialize_stage(ctx, {"k": "v"}, {"tool": "dummy"})
            finalize_stage(ctx, {"m": 1}, [{"id": "x"}], {"extra": True})
            for name in MANDATORY_STAGE_FILES:
                self.assertTrue((ctx.stage_dir / name).exists())
            self.assertTrue(stage_completed(ctx.stage_dir))


if __name__ == "__main__":
    unittest.main()
