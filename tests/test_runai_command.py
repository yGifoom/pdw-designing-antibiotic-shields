import unittest
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


if __name__ == '__main__':
    unittest.main()
