# Lane-1 Cluster-Native Protein Binder Design Pipeline (EPFL RCP + RunAI)

This repository implements a **modular, resumable, stage-based lane-1 pipeline** for direct structure-based binder design using separate RunAI jobs per heavy stage (RFdiffusion3, LigandMPNN, AF3), with a lightweight Python orchestrator.

## Scope (Lane 1 only)
1. prepare target
2. define hotspots (read from RFdiffusion JSON configs)
3. generate binder backbones with RFdiffusion3
4. design sequences with LigandMPNN
5. AF3 scoring
6. first-pass ranking / clustering / filtering
7. optional rediffusion hit expansion
8. redesign sequences
9. AF3 rescoring
10. final ESM annotation
11. final ranking and reporting

## Repository Structure
- `configs/` run configs (fast/thorough presets)
- `pipeline/` orchestrator, config schema, stage definitions, RunAI command builder
- `stages/` stage contract documentation + concrete tool hooks
- `cluster/` reusable RunAI templates/helpers
- `docs/` hotspot schema + output schema conventions
- `examples/` sample hotspot YAML (optional/manual fallback)
- `tests/` lightweight validation tests

## EPFL RCP / RunAI Assumptions
- Jobs are submitted with `runai submit`.
- **1 GPU per stage job**.
- Stage-specific images:
  - RFdiffusion3: `registry.rcp.epfl.ch/proteindesign-containers/rfd3:2026.1`
  - LigandMPNN: `registry.rcp.epfl.ch/proteindesign-containers/ligandmpnn:2026.1`
  - AlphaFold3: `registry.rcp.epfl.ch/proteindesign-containers/af3:2026.1`
- PVC mounts:
  - scratch read/write at `/mnt/scratch`
  - shared read-only at `/mnt/shared-ro`
- Container-local filesystem is ephemeral.
- Persistent outputs/logs/results/reports are written under `/mnt/scratch`.

## 1) Set / use your RunAI project

```bash
runai config project pdw
# or pass --project pdw in each command
```

Also set namespace explicitly in submit commands (`--namespace protein-design`) or your site default namespace.

## 2) Scratch and shared storage mounts
All stage jobs should mount:
- `--pvc pdw-scratch-pvc:/mnt/scratch`
- `--pvc pdw-shared-ro-pvc:/mnt/shared-ro:ro`

Important path context:
- `/mnt/scratch` is typically the **in-container** mount path used by submitted RunAI jobs.
- If you run the orchestrator/launcher from an SSH/login host, set `scratch_root` (or `SCRATCH_ROOT`) to your **host-visible** scratch path (for example `/mnt/hackathon-proteindesign/.../scratch-gXX/<project>`).

## 3) Stage-image mapping
- `03_rfd3_backbones` + `07_optional_rediffusion`: RFdiffusion3 image
- `04_ligandmpnn_design` + `08_redesign_sequences`: LigandMPNN image
- `05_af3_score_pass1` + `09_af3_rescore_pass2`: AF3 image
- lightweight metadata/report stages: orchestrator image (default `python:3.11-slim`)

## 4) Example `runai submit` commands

### RFdiffusion3 stage
```bash
runai submit lane1-rfd3 \
  --project pdw \
  --namespace protein-design \
  --image registry.rcp.epfl.ch/proteindesign-containers/rfd3:2026.1 \
  --gpu 1 --cpu 8 --memory 32Gi \
  --pvc pdw-scratch-pvc:/mnt/scratch \
  --pvc pdw-shared-ro-pvc:/mnt/shared-ro:ro \
  --command -- bash -lc 'rfd3 design out_dir=/mnt/scratch/pdw-lane1/rfd3/out inputs=/mnt/scratch/pdw-lane1/rfd3/input.json ckpt_path=${CKPT_PATH} n_batches=1 diffusion_batch_size=2'
```

### LigandMPNN stage
```bash
runai submit lane1-ligandmpnn \
  --project pdw \
  --namespace protein-design \
  --image registry.rcp.epfl.ch/proteindesign-containers/ligandmpnn:2026.1 \
  --gpu 1 --cpu 8 --memory 32Gi \
  --pvc pdw-scratch-pvc:/mnt/scratch \
  --pvc pdw-shared-ro-pvc:/mnt/shared-ro:ro \
  --command -- bash -lc 'cd /opt/LigandMPNN && python run.py --model_type protein_mpnn --checkpoint_protein_mpnn /opt/LigandMPNN/model_params/proteinmpnn_v_48_020.pt --pdb_path /mnt/scratch/pdw-lane1/ligandmpnn/input/example.pdb --out_folder /mnt/scratch/pdw-lane1/ligandmpnn/output/example --number_of_batches 1 --batch_size 8'
```

### AF3 stage
```bash
runai submit lane1-af3 \
  --project pdw \
  --namespace protein-design \
  --image registry.rcp.epfl.ch/proteindesign-containers/af3:2026.1 \
  --gpu 1 --cpu 8 --memory 48Gi \
  --pvc pdw-scratch-pvc:/mnt/scratch \
  --pvc pdw-shared-ro-pvc:/mnt/shared-ro:ro \
  --command -- bash -lc 'python /opt/alphafold3/run_alphafold.py --json_path /mnt/scratch/pdw-lane1/af3/example/input.json --model_dir /mnt/scratch/af3_weights --output_dir /mnt/scratch/pdw-lane1/af3/example/output --jax_compilation_cache_dir /mnt/scratch/af3_jax_cache --norun_data_pipeline'
```

## 5) Run the Python orchestrator (submits stage jobs)

Dry run (prints RunAI commands, does not submit):
```bash
python -m pipeline.orchestrator --config configs/lane1.fast.yaml --dry-run
```

In dry-run mode, the orchestrator does not create scratch directories or write run artifacts.

Submit real jobs:
```bash
python -m pipeline.orchestrator --config configs/lane1.thorough.yaml
```

Behavior:
- reads YAML config
- resolves run root `<scratch_root>/<run_id>`
- respects stage dependencies
- submits stage jobs per stage image
- skips completed stages
- resumes partial runs
- supports fast/thorough presets

## 6) Inspect/manage jobs
```bash
runai list jobs
runai describe job <job-name>
runai attach <job-name>
runai delete job <job-name>
```

## 7) Output location layout
Under `/mnt/scratch`:

```text
<scratch_root>/<run_id>/
  run_manifest.json
  orchestrator_state.json
  01_prepare_target/
  02_define_hotspots/
  ...
  11_final_rank_report/
```

Each stage directory must include:
- `status.json`
- `params.json`
- `metrics.json`
- `provenance.json`
- `stdout.log`
- `stderr.log`
- `summary.csv` (or plus parquet)
- `validation.json`

## 8) Safe resume of partial runs
Re-run the same orchestrator command with the same `run_id`.
- completed stages with valid mandatory outputs are skipped
- incomplete/missing outputs are rerun
- dependency graph prevents downstream execution when prerequisites are not complete

## Hotspots (from RFdiffusion JSON)
The pipeline now resolves hotspots directly from RFdiffusion input JSON files (no separate YAML required).

Supported RFdiffusion input sources:
- `RFD3_INPUT_JSON_LIST` (comma-separated explicit JSON paths)
- `RFD3_INPUT_JSON` (single JSON path)
- `RFD3_INPUT_JSON_GLOB` (glob pattern)
- `stage_overrides.03_rfd3_backbones.params.rfd3_input_jsons` (YAML list)
- `stage_overrides.03_rfd3_backbones.params.rfd3_input_glob` (YAML glob)

`02_define_hotspots` extracts hotspot-like fields from these JSON files and writes normalized hotspot metadata for downstream reporting.

## AF3 + ranking/filtering metric model
First-pass and second-pass scoring/filters include:
- AF3 metrics: `pTM`, `ipTM`, `ipSAE`
- RFD3/design agreement: pose retention, interface geometry agreement, optional RMSD-to-design, clash-free interface

Pipeline supports:
- hard thresholds (pass/fail)
- soft weighted ranking
- composite ranking scores
- representative selection using these metrics

`ipSAE` is first-class in pass-1 filter, pass-2 filter, representative selection, and final reports.

## Compute efficiency strategy
- early AF3 triage
- aggressive first-pass clustering (especially in fast mode)
- carry only representatives to rediffusion
- second-pass expansion/refinement only on shortlisted families

## Fast vs thorough presets
- **Fast**: fewer backbones/sequences, aggressive clustering, small shortlist, rapid diagnostics.
- **Thorough**: broader generation/refinement, larger shortlist, stricter validation.

## RunAI templates included
- Generic stage submit: `cluster/templates/stage_submit.sh`
- Interactive debug job: `cluster/templates/interactive_debug.sh`
- Example per image:
  - `cluster/templates/rfd3_example.sh`
  - `cluster/templates/ligandmpnn_example.sh`
  - `cluster/templates/af3_example.sh`

## Pipeline launcher script
A configurable end-to-end launcher is provided:

```bash
./scripts/run_pipeline.sh
```

Key env vars:
- `RUNAI_PROJECT`, `RUNAI_NAMESPACE`, `SCRATCH_PVC`, `SHARED_RO_PVC`
- `TARGET_INPUT`, `CKPT_PATH` (or `RFD3_CKPT_PATH`)
- `LIGANDMPNN_CHECKPOINT` (MPNN model checkpoint path)
- `AF3_MODEL_DIR`, `AF3_JAX_CACHE_DIR`
- `RFD3_INPUT_JSON_GLOB` or `RFD3_INPUT_JSON_LIST`
- `PRESET` (`fast`/`thorough`), `RUN_ID`, `SCRATCH_ROOT`
- `DRY_RUN_ONLY=1` for dry-run submit generation only

## Development
```bash
python -m unittest discover -s tests
```

## Tool integration implementation notes
Tool hooks are now wired for RFdiffusion3, LigandMPNN and AF3 with commands adapted from the sample EPFL pipeline.

Notes:
- `03_rfd3_backbones` and `07_optional_rediffusion` require `CKPT_PATH` or `RFD3_CKPT_PATH`.
- LigandMPNN stages use `LIGANDMPNN_CHECKPOINT` (default `/opt/LigandMPNN/model_params/proteinmpnn_v_48_020.pt`).
- AF3 stages use `AF3_MODEL_DIR` and `AF3_JAX_CACHE_DIR`.
- For multi-target / multi-length RFdiffusion sweeps, set one of:
  - `RFD3_INPUT_JSON_LIST` (comma-separated explicit JSON paths)
  - `RFD3_INPUT_JSON_GLOB` (glob pattern)
  - `stage_overrides.03_rfd3_backbones.params.rfd3_input_jsons` (YAML list)
  - `stage_overrides.03_rfd3_backbones.params.rfd3_input_glob` (YAML glob)
- LigandMPNN stages expect PDB inputs in `LIGANDMPNN_INPUT_DIR` (default stage-local `input/`).
- AF3 stages synthesize input JSON from FASTA and parse `*_summary_confidences.json` into `pTM`, `ipTM`, and `ipSAE`.
- `10_esm_annotation` produces `esm_score` as pseudo-perplexity annotation and tie-breaker metadata.
