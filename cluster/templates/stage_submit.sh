#!/usr/bin/env bash
set -euo pipefail

# Generic RunAI stage submit template for EPFL RCP (1 GPU/job).
# Usage:
#   ./cluster/templates/stage_submit.sh <job-name> <project> <image> <scratch-pvc> <shared-ro-pvc> <command>

JOB_NAME="$1"
PROJECT="$2"
IMAGE="$3"
SCRATCH_PVC="$4"
SHARED_RO_PVC="$5"
CMD="$6"

runai submit --name "$JOB_NAME" \
  --project "$PROJECT" \
  --image "$IMAGE" \
  --gpu 1 \
  --cpu 8 \
  --memory 32Gi \
  --pvc "${SCRATCH_PVC}:/mnt/scratch" \
  --pvc "${SHARED_RO_PVC}:/mnt/shared-ro:ro" \
  --backoff-limit 0 \
  --command -- bash -lc "$CMD"
