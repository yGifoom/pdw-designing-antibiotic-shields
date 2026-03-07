#!/usr/bin/env bash
set -euo pipefail

# Interactive debug shell on EPFL RCP.
# Usage:
#   ./cluster/templates/interactive_debug.sh <job-name> <project> <namespace> <image> <scratch-pvc> <shared-ro-pvc>

JOB_NAME="$1"
PROJECT="$2"
NAMESPACE="$3"
IMAGE="$4"
SCRATCH_PVC="$5"
SHARED_RO_PVC="$6"

runai submit "$JOB_NAME" \
  --project "$PROJECT" \
  --namespace "$NAMESPACE" \
  --image "$IMAGE" \
  --interactive \
  --gpu 1 \
  --cpu 4 \
  --memory 16Gi \
  --pvc "${SCRATCH_PVC}:/mnt/scratch" \
  --pvc "${SHARED_RO_PVC}:/mnt/shared-ro:ro" \
  --command -- bash
