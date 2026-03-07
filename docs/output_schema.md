# Output Schema Conventions

Persistent root:
- `<scratch_root>/<run_id>/`

Per-stage directory:
- `<scratch_root>/<run_id>/<stage_name>/`

Required diagnostic artifacts:
- `status.json`
- `params.json`
- `metrics.json`
- `provenance.json`
- `stdout.log`
- `stderr.log`
- `summary.csv` (optionally add `summary.parquet`)
- `validation.json`

## Candidate-level final table fields
- `candidate_id`
- `run_id`
- `hotspot_id`
- `hotspot_source`
- `hotspot_label`
- `parent_backbone_id`
- `lineage_first_pass`
- `lineage_second_pass`
- `pTM`
- `ipTM`
- `ipSAE`
- `pose_retention`
- `interface_geometry_agreement`
- `optional_rmsd_to_design`
- `clash_free_interface`
- `esm_score`
- `final_rank`
- `structure_path`
- `diagnostics_path`

## Pass/fail and ranking
Each stage that filters candidates should emit:
- hard-threshold pass/fail booleans for `pTM`, `ipTM`, `ipSAE`, pose-retention, geometry agreement, clash-free interface.
- soft composite score from configurable weights.
- representative cluster assignment and representative flag.

`ipSAE` must be treated as first-class in pass-1, pass-2, representative selection, and final reports.
