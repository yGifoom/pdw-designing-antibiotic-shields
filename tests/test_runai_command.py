import unittest
from unittest.mock import patch
from pathlib import Path

from pipeline.config import ClusterConfig, StageConfig
from pipeline.runai import RunaiJobSpec, build_submit_command


class RunaiCommandTests(unittest.TestCase):
    def test_submit_command_compatible_flags(self) -> None:
        spec = RunaiJobSpec(
            name='job1',
            image='img',
            command='echo hi',
            stage_cfg=StageConfig(),
            cluster=ClusterConfig(project='proj', namespace='ignored', scratch_pvc='s', shared_ro_pvc='r'),
            run_root=Path('/tmp/run'),
        )
        cmd = build_submit_command(spec)
        self.assertIn('--name', cmd)
        self.assertNotIn('--namespace', cmd)
        self.assertNotIn('--active-deadline-seconds', cmd)

    def test_active_deadline_flag_opt_in(self) -> None:
        spec = RunaiJobSpec(
            name='job1',
            image='img',
            command='echo hi',
            stage_cfg=StageConfig(timeout_minutes=5),
            cluster=ClusterConfig(project='proj', namespace='ignored', scratch_pvc='s', shared_ro_pvc='r'),
            run_root=Path('/tmp/run'),
        )
        with patch.dict('os.environ', {'RUNAI_ENABLE_ACTIVE_DEADLINE': '1'}):
            cmd = build_submit_command(spec)
        self.assertIn('--active-deadline-seconds', cmd)


if __name__ == '__main__':
    unittest.main()
