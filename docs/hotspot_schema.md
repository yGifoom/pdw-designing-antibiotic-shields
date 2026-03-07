# Manual Hotspot Specification Schema

Top-level YAML key: `hotspots` (list).

Each hotspot requires:
- `hotspot_id` (string)
- `label` (string)
- `source` (`manual`)
- `mode` one of:
  - `residue_list`
  - `residue_range`
  - `center_radius`
  - `chain_residues`
- `payload` (mode-dependent mapping)

Payload variants:
- `residue_list`: `chain`, `residues: [int, ...]`
- `residue_range`: `chain`, `start`, `end`
- `center_radius`: `center_xyz: [x,y,z]`, `radius_angstrom`
- `chain_residues`: `chain_residue_ids: ["A:12", "B:55", ...]`

Hotspot metadata (`hotspot_id`, `label`, `source`) must be propagated through downstream outputs and final ranking tables.
