# Lane 2 Architecture

The orchestrator is intentionally lightweight and drives a stage DAG that is linear by default.
Heavy tool stages must run in dedicated images and can be submitted independently to a cluster.

## Design goals
- Modular stage boundaries
- Resume + rerun safety
- Rich diagnostics in every stage output folder
- One GPU per heavy stage job
- Coarse-to-fine filtering to minimize expensive scoring load

## Cluster-native assumptions
- Scratch mounted at `<scratch_root>/<run_id>`
- Stage image selected per stage
- GPU jobs are isolated and queueable with `gpu: 1`
- CPU stages remain `gpu: 0`

