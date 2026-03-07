#!/usr/bin/env bash
set -euo pipefail

# Example LigandMPNN stage submission (non-interactive)
runai submit lane1-ligandmpnn-example \
  --project pdw \
  --namespace protein-design \
  --image registry.rcp.epfl.ch/proteindesign-containers/ligandmpnn:2026.1 \
  --gpu 1 --cpu 8 --memory 32Gi \
  --pvc pdw-scratch-pvc:/mnt/scratch \
  --pvc pdw-shared-ro-pvc:/mnt/shared-ro:ro \
  --command -- bash -lc 'cd /opt/LigandMPNN && for PDB in /mnt/scratch/pdw-lane1/ligandmpnn/input/*.pdb; do B=$(basename "$PDB" .pdb); python run.py --model_type protein_mpnn --checkpoint_protein_mpnn /opt/LigandMPNN/model_params/proteinmpnn_v_48_020.pt --pdb_path "$PDB" --out_folder /mnt/scratch/pdw-lane1/ligandmpnn/output/$B --number_of_batches 1 --batch_size 8; done'
