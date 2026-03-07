# Hotspot Extraction Schema (RFdiffusion JSON-first)

Primary behavior:
- The pipeline extracts hotspots directly from RFdiffusion input JSON files.
- A separate hotspot YAML file is **not required**.

Supported RFdiffusion input selectors:
- `RFD3_INPUT_JSON_LIST` (comma-separated JSON paths)
- `RFD3_INPUT_JSON` (single JSON path)
- `RFD3_INPUT_JSON_GLOB` (glob)
- `stage_overrides.03_rfd3_backbones.params.rfd3_input_jsons` (YAML list)
- `stage_overrides.03_rfd3_backbones.params.rfd3_input_glob` (YAML glob)

Stage `02_define_hotspots` recursively scans RFdiffusion JSON payloads and extracts hotspot-like keys:
- `hotspots`
- `hotspot`
- `interface_hotspots`
- `binding_hotspots`

Normalized downstream fields:
- `hotspot_id`
- `label`
- `source` (originating JSON path)
- `mode` (`json_payload`)
- `payload` (verbatim extracted hotspot object)

Hotspot metadata (`hotspot_id`, `label`, `source`) is propagated for downstream reporting.
