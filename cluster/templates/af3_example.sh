#!/usr/bin/env bash
set -euo pipefail

# Example AlphaFold3 stage submission (non-interactive)
runai submit --name lane1-af3-example \
  --project hackathon-proteindesign-santanto \
  --image registry.rcp.epfl.ch/proteindesign-containers/af3:2026.1 \
  --gpu 1 --cpu 8 --memory 48Gi \
  --pvc pdw-scratch-pvc:/mnt/scratch \
  --pvc pdw-shared-ro-pvc:/mnt/shared-ro:ro \
  --command -- bash -lc 'python /opt/alphafold3/run_alphafold.py --json_path /mnt/scratch/pdw-lane1/af3/example/input.json --model_dir /mnt/scratch/af3_weights --output_dir /mnt/scratch/pdw-lane1/af3/example/output --jax_compilation_cache_dir /mnt/scratch/af3_jax_cache --norun_data_pipeline'
