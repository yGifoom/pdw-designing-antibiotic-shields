#!/usr/bin/env bash
set -euo pipefail

# Configurable launcher for full lane-1 pipeline.
# Usage:
#   RUNAI_PROJECT=... RUNAI_NAMESPACE=... SCRATCH_PVC=... SHARED_RO_PVC=... TARGET_INPUT=... \
#   RFD3_CKPT_PATH=... LIGANDMPNN_CHECKPOINT=... AF3_MODEL_DIR=... AF3_JAX_CACHE_DIR=... \
#   ./scripts/run_pipeline.sh

RUN_ID="${RUN_ID:-lane1-$(date +%Y%m%d-%H%M%S)}"
PRESET="${PRESET:-fast}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mnt/scratch/pdw-lane1}"
TARGET_INPUT="${TARGET_INPUT:-/mnt/shared-ro/targets/target_a.pdb}"

RUNAI_PROJECT="${RUNAI_PROJECT:-pdw}"
RUNAI_NAMESPACE="${RUNAI_NAMESPACE:-protein-design}"
SCRATCH_PVC="${SCRATCH_PVC:-pdw-scratch-pvc}"
SHARED_RO_PVC="${SHARED_RO_PVC:-pdw-shared-ro-pvc}"

RFD3_IMAGE="${RFD3_IMAGE:-registry.rcp.epfl.ch/proteindesign-containers/rfd3:2026.1}"
LIGANDMPNN_IMAGE="${LIGANDMPNN_IMAGE:-registry.rcp.epfl.ch/proteindesign-containers/ligandmpnn:2026.1}"
AF3_IMAGE="${AF3_IMAGE:-registry.rcp.epfl.ch/proteindesign-containers/af3:2026.1}"
ORCH_IMAGE="${ORCH_IMAGE:-python:3.11-slim}"

RFD3_INPUT_JSON_GLOB="${RFD3_INPUT_JSON_GLOB:-/mnt/scratch/pdw-lane1/rfd3_inputs/${PRESET}/*.json}"
RFD3_INPUT_JSON_LIST="${RFD3_INPUT_JSON_LIST:-}"

LIGANDMPNN_CHECKPOINT="${LIGANDMPNN_CHECKPOINT:-/opt/LigandMPNN/model_params/proteinmpnn_v_48_020.pt}"
AF3_MODEL_DIR="${AF3_MODEL_DIR:-/mnt/scratch/af3_weights}"
AF3_JAX_CACHE_DIR="${AF3_JAX_CACHE_DIR:-/mnt/scratch/af3_jax_cache}"

if [[ -z "${CKPT_PATH:-${RFD3_CKPT_PATH:-}}" ]]; then
  echo "ERROR: CKPT_PATH (or RFD3_CKPT_PATH) must be set" >&2
  exit 1
fi
if [[ -z "${LIGANDMPNN_CHECKPOINT}" ]]; then
  echo "ERROR: LIGANDMPNN_CHECKPOINT must be set" >&2
  exit 1
fi
if [[ -z "${AF3_MODEL_DIR}" ]]; then
  echo "ERROR: AF3_MODEL_DIR must be set" >&2
  exit 1
fi

TMP_CONFIG="${TMP_CONFIG:-/tmp/lane1.${RUN_ID}.yaml}"
cat > "$TMP_CONFIG" <<YAML
run_id: ${RUN_ID}
preset: ${PRESET}
scratch_root: ${SCRATCH_ROOT}
target_input: ${TARGET_INPUT}

cluster:
  project: ${RUNAI_PROJECT}
  namespace: ${RUNAI_NAMESPACE}
  scratch_mount: /mnt/scratch
  shared_ro_mount: /mnt/shared-ro
  scratch_pvc: ${SCRATCH_PVC}
  shared_ro_pvc: ${SHARED_RO_PVC}

images:
  orchestrator: ${ORCH_IMAGE}
  rfd3: ${RFD3_IMAGE}
  ligandmpnn: ${LIGANDMPNN_IMAGE}
  af3: ${AF3_IMAGE}

stage_overrides:
  03_rfd3_backbones:
    params:
      rfd3_input_glob: ${RFD3_INPUT_JSON_GLOB}
YAML

if [[ -n "$RFD3_INPUT_JSON_LIST" ]]; then
  export RFD3_INPUT_JSON_LIST
fi
if [[ -n "$RFD3_INPUT_JSON_GLOB" ]]; then
  export RFD3_INPUT_JSON_GLOB
fi
export LIGANDMPNN_CHECKPOINT
export AF3_MODEL_DIR
export AF3_JAX_CACHE_DIR

echo "[lane1] Config written: $TMP_CONFIG"
echo "[lane1] RFD3 checkpoint: ${CKPT_PATH:-${RFD3_CKPT_PATH:-}}"
echo "[lane1] LigandMPNN checkpoint: ${LIGANDMPNN_CHECKPOINT}"
echo "[lane1] AF3 model dir: ${AF3_MODEL_DIR}"
echo "[lane1] scratch_root: ${SCRATCH_ROOT}"
echo "[lane1] PIPELINE_LOCAL_STATE=${PIPELINE_LOCAL_STATE:-0} (set to 1 only if launcher host can write scratch_root)"
if [[ "$SCRATCH_ROOT" == /mnt/scratch/* ]]; then
  echo "[lane1] NOTE: /mnt/scratch is usually container-internal. If running launcher on SSH/login host,"
  echo "[lane1]       set SCRATCH_ROOT to your host-visible scratch path, e.g."
  echo "[lane1]       /mnt/hackathon-proteindesign/.../scratch-gXX/<project>."
fi
python -m pipeline.orchestrator --config "$TMP_CONFIG" --dry-run

if [[ "${DRY_RUN_ONLY:-0}" == "1" ]]; then
  echo "[lane1] DRY_RUN_ONLY=1 set; stopping after dry-run"
  exit 0
fi

python -m pipeline.orchestrator --config "$TMP_CONFIG"
echo "[lane1] Submitted. Outputs root: ${SCRATCH_ROOT}/${RUN_ID}"
