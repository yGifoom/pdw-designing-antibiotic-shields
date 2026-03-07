# Dynamics-Aware Binder Design Pipeline (Lane 2 Only)

This repository implements a **production-quality, modular, stage-based, cluster-native pipeline** focused exclusively on **lane 2 (dynamics-aware binder design)**.

> Design principle: one lightweight Python orchestrator coordinates many independent stage jobs, where heavy model stages run in isolated stage-specific jobs/images with a **1 GPU per job** constraint.

---

## 1) Scope: Lane 2 stages implemented

The pipeline is organized as the following run stages:

1. `01_prepare_target`
2. `02_bioemu_generate`
3. `03_bioemu_cluster`
4. `04_hotspot_detect`
5. `05_hotspot_select`
6. `06_generate_backbones`
7. `07_design_seq_ligandmpnn`
8. `08_design_seq_carbonara`
9. `09_af3_score`
10. `10_rank_first_pass`
11. `11_select_rediffusion_seeds`
12. `12_rediffusion`
13. `13_seq_redesign`
14. `14_af3_rescore`
15. `15_bioemu_candidate_sanity`
16. `16_esm_annotate`
17. `17_final_rank`
18. `18_report`

All stages are present as modular Python stage modules and can be run independently or via orchestrator subsets.

---

## 2) Repository structure

```text
configs/                    # YAML configuration presets and examples
pipeline/                   # Orchestrator, contracts, schemas, diagnostics, utilities
stages/                     # One module per stage (01..18)
cluster/                    # Generic cluster abstraction and template emitters
env/                        # Stage image and environment metadata templates
docs/                       # Architecture notes and output schema docs
examples/                   # Example hotspot specifications and walkthrough data
tests/                      # Lightweight unit tests for planner/config behavior
```

---

## 3) Cluster model (1 GPU per job)

- The orchestrator never embeds heavy model compute.
- Each stage declares:
  - `image`
  - `gpu` requirement (`0` or `1`)
  - CPU/memory estimates
  - command payload
- GPU stages are serialized as one stage/job at a time by default, and each such stage requests exactly one GPU.
- CPU stages remain CPU-only.
- Cluster backend is abstracted (`local`, `slurm-template` now) and easy to extend.

See:
- `cluster/cluster_backend.py`
- `cluster/slurm_template.py`
- `env/stage_images.yaml`

---

## 4) Run-oriented output layout

Each run writes under:

```text
<scratch_root>/<run_id>/
```

With stage directories:

```text
01_prepare_target/
02_bioemu_generate/
03_bioemu_cluster/
04_hotspot_detect/
05_hotspot_select/
06_generate_backbones/
07_design_seq_ligandmpnn/
08_design_seq_carbonara/
09_af3_score/
10_rank_first_pass/
11_select_rediffusion_seeds/
12_rediffusion/
13_seq_redesign/
14_af3_rescore/
15_bioemu_candidate_sanity/
16_esm_annotate/
17_final_rank/
18_report/
```

Plus global run artifacts:

- `config.snapshot.yaml`
- `run_manifest.json`
- `stage_index.csv`
- `candidate_lineage.csv`

---

## 5) Stage contracts and diagnostics

Every stage:

- reads declared inputs from prior stage directories
- writes all outputs to its own stage directory
- is safe to rerun
- supports skip/resume (`status.json` + validation)
- validates required outputs before completion

Every stage writes diagnostics:

- `status.json`
- `params.json`
- `metrics.json`
- `provenance.json`
- `stdout.log`
- `stderr.log`
- `summary.csv`
- `validation.json`

Where useful, stage modules can also emit additional plot/visual files (`*.png`, `*.svg`) and rich per-candidate tables.

---

## 6) Hotspot modes: manual / auto / hybrid

Configured in `hotspot.mode`:

- `manual`: only user-specified hotspots are used
- `auto`: hotspots are generated from representative BioEmu conformers
- `hybrid`: manual + auto merged, deduplicated, source labels preserved

Manual hotspot schema supports:

- residue lists
- residue ranges
- center + radius
- chain + residue IDs
- labels (`active_site`, `substrate_tunnel`, `loop_gate`, etc.)

See:

- `pipeline/hotspot_schema.py`
- `examples/hotspots/manual_hotspots.yaml`

---

## 7) Automatic hotspot scoring model

The auto hotspot stage (`04_hotspot_detect`) integrates configurable weighted components:

- pocket score
- PeSTo score
- conservation score
- catalytic prior score
- ligand-context score
- exposure persistence across BioEmu states

Workflow:

1. pocket detection summaries
2. per-residue PeSTo maps
3. optional conservation/catalytic/ligand maps
4. candidate patch construction
5. weighted patch scoring
6. overlap clustering + redundancy removal
7. ranked hotspot output with keep/drop rationale and provenance

All component values and total weighted scores are persisted in `summary.csv` and `metrics.json`.

> Current implementation includes placeholders/TODO call sites for external tool invocation.

---

## 8) AF3 metrics and first-pass filtering (explicit)

The AF3 scoring stage emits first-class metrics including:

- `pTM`
- `ipTM`
- `ipSAE`
- binder confidence (e.g., mean binder pLDDT proxy)
- interface/contact metrics
- pose-retention metrics vs RFD3 design hypothesis
- clash/interface checks
- raw + normalized metrics and pass/fail flags

First-pass filtering (`10_rank_first_pass`) supports:

- min/max thresholds per metric
- hard filters
- weighted composite ranking
- per-metric pass/fail flags
- diversity-aware selection hooks

`ipSAE` is explicitly included as an important interface-confidence signal.

---

## 9) BioEmu monomer sanity stage (explicit)

Stage `15_bioemu_candidate_sanity` evaluates AF3-shortlisted binder sequences as monomers with metrics:

- fold occupancy
- helix occupancy
- sheet occupancy
- radius compactness
- competing fold basins

Configurable options include:

- ensemble size
- RMSD thresholds
- clustering settings for competing basins
- secondary-structure persistence thresholds

Diagnostics include RMSD distributions, occupancy summaries, compactness summaries, cluster summaries, and keep/drop rationale.

---

## 10) Final filtering/ranking metric set

Final ranking combines:

- AF3 metrics (`pTM`, `ipTM`, `ipSAE`)
- RFD3 validation metrics (pose retention, interface agreement, optional RMSD-to-design)
- BioEmu sanity metrics (fold/helix/sheet occupancy, compactness, competing basins)
- ESM annotation as tie-breaker/outlier signal

Hard filters and weighted ranking are configurable.

---

## 11) Fast vs thorough presets

Two presets are built in:

- `fast` (exploratory): fewer samples/states/hotspots/backbones; aggressive clustering; short iteration loops
- `thorough` (production-like): larger sampling and broader carry-through with stricter validation

Preset behavior is defined in `pipeline/presets.py` and selected in YAML.

---

## 12) Launching runs

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r env/requirements.txt
```

### Dry run plan

```bash
python -m pipeline.orchestrator \
  --config configs/minimal_fast.yaml \
  --scratch-root /tmp/pipeline_runs \
  --run-id demo_fast \
  --dry-run
```

### Execute full run

```bash
python -m pipeline.orchestrator \
  --config configs/full_thorough.yaml \
  --scratch-root /tmp/pipeline_runs \
  --run-id demo_thorough
```

### Resume a partial run

Re-run same command with same `run_id`; completed validated stages are skipped automatically.

### Run subset of stages

```bash
python -m pipeline.orchestrator \
  --config configs/minimal_fast.yaml \
  --scratch-root /tmp/pipeline_runs \
  --run-id demo_subset \
  --start-stage 04_hotspot_detect \
  --end-stage 10_rank_first_pass
```

---

## 13) Example configs

- Minimal config: `configs/minimal_fast.yaml`
- Complete config: `configs/full_thorough.yaml`

These include:

- stage resource/image mapping
- hotspot mode + scoring weights
- AF3 threshold and ranking definitions
- BioEmu sanity thresholds
- final ranking rules

---

## 14) Example walkthrough

See `docs/walkthrough.md` for a full flow from target preparation through final report inspection, including where to inspect diagnostics and how to compare runs.

---

## 15) Validation and failure handling

- Stage completion is gated by output validation.
- Failed validations mark stage as failed and preserve logs.
- Stages are rerunnable safely.
- Orchestrator resume logic skips completed validated stages and reattempts failed/incomplete stages.

---

## 16) Extending stage internals

This repository intentionally provides architecture and robust orchestration scaffolding.
External heavy tool invocation points are marked with `TODO(tool-integration)` in stage implementations.

Replace placeholder generation/metric code with production integrations while keeping contracts and diagnostics unchanged.

