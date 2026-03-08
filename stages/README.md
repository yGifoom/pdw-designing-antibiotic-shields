# Stage Interfaces (Lane 1)

Each stage must be standalone and resumable under `<scratch_root>/<run_id>/<stage_name>/`.

Required files for every stage:
- `status.json`
- `params.json`
- `metrics.json`
- `provenance.json`
- `stdout.log`
- `stderr.log`
- `summary.csv` (or stage-specific `.parquet` companion)
- `validation.json`

## Stage list
1. `01_prepare_target`
2. `02_define_hotspots` (extract from RFdiffusion JSON inputs)
3. `03_rfd3_backbones`
4. `04_ligandmpnn_design`
5. `05_af3_score_pass1`
6. `06_rank_cluster_filter_pass1`
7. `07_optional_rediffusion`
8. `08_redesign_sequences`
9. `09_af3_rescore_pass2`
10. `10_esm_annotation`
11. `11_final_rank_report`

## Implemented tool invocations
- RFdiffusion3 stages call `rfd3 design out_dir=... inputs=... ckpt_path=... n_batches=... diffusion_batch_size=...` and support multiple input JSON files per stage via `RFD3_INPUT_JSON_LIST`, `RFD3_INPUT_JSON_GLOB`, `params.rfd3_input_jsons`, or `params.rfd3_input_glob`.
- LigandMPNN stages call `/opt/LigandMPNN/run.py` with `protein_mpnn` model and checkpoint `/opt/LigandMPNN/model_params/proteinmpnn_v_48_020.pt`.
- AF3 stages generate per-sequence input JSONs and call `/opt/alphafold3/run_alphafold.py` with `--norun_data_pipeline`, model dir `/mnt/scratch/af3_weights`, and cache `/mnt/scratch/af3_jax_cache`.
- ESM annotation stage computes a pseudo-perplexity score (stored as `esm_score`) for shortlisted candidates and appends it into stage output tables.
