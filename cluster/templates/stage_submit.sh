#!/usr/bin/env bash
set -euo pipefail

# Generic RunAI stage submit template for EPFL RCP (1 GPU/job).
# Usage:
#   ./cluster/templates/stage_submit.sh <job-name> <project> <namespace> <image> <scratch-pvc> <shared-ro-pvc> <command>

JOB_NAME="$1"
PROJECT="$2"
NAMESPACE="$3"
IMAGE="$4"
SCRATCH_PVC="$5"
SHARED_RO_PVC="$6"
CMD="$7"

runai submit "$JOB_NAME" \
  --project "$PROJECT" \
  --namespace "$NAMESPACE" \
  --image "$IMAGE" \
  --gpu 1 \
  --cpu 8 \
  --memory 32Gi \
  --pvc "${SCRATCH_PVC}:/mnt/scratch" \
  --pvc "${SHARED_RO_PVC}:/mnt/shared-ro:ro" \
  --backoff-limit 0 \
  --command -- bash -lc "$CMD"
