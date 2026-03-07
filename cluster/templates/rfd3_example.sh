#!/usr/bin/env bash
set -euo pipefail

# Example RFdiffusion3 stage submission (non-interactive)
runai submit --name lane1-rfd3-example \
  --project pdw \
  --image registry.rcp.epfl.ch/proteindesign-containers/rfd3:2026.1 \
  --gpu 1 --cpu 8 --memory 32Gi \
  --pvc pdw-scratch-pvc:/mnt/scratch \
  --pvc pdw-shared-ro-pvc:/mnt/shared-ro:ro \
  --command -- bash -lc 'mkdir -p /mnt/scratch/pdw-lane1/rfd3 && rfd3 design out_dir=/mnt/scratch/pdw-lane1/rfd3/out inputs=/mnt/scratch/pdw-lane1/rfd3/input.json ckpt_path=${CKPT_PATH} n_batches=1 diffusion_batch_size=2'
