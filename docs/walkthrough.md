# Walkthrough (example)

1. Run dry-run against `configs/minimal_fast.yaml`.
2. Execute the full run with the same run ID.
3. Inspect stage diagnostics under `<scratch_root>/<run_id>/04_hotspot_detect` for hotspot details.
4. Inspect `<scratch_root>/<run_id>/09_af3_score/summary.csv` and `10_rank_first_pass/summary.csv` to evaluate AF3 triage.
5. Inspect `15_bioemu_candidate_sanity` for fold occupancy and competing basin diagnostics.
6. Read `17_final_rank/summary.csv` and `18_report/report.md`.

