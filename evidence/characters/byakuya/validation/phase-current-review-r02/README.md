# Byakuya phase-current independent review r02

The three first `boundary-r11-current-missing5` cases were rechecked using the project-standard parser `tools/probes/collect_ai_reference.py`. The retained raw `AIREF|...` gzip files were left unchanged. The parser output is retained under `source/<case>/events.jsonl`; strict comparisons are under `compare/`.

All three cases completed a 300-fight-tick collection and strict comparison:

- `byakuya-123-airhit-neutral`: 602/602 fighter states, `matched`, `acceptance_status=validated`, 0 differences.
- `byakuya-139-airMagichit-neutral`: 602/602, `matched`, `acceptance_status=validated`, 0 differences.
- `byakuya-849-defence-neutral`: 602/602, `matched`, `acceptance_status=validated`, 0 differences.

Each build has `frame_order_probe=false`, `recovery_order_probe=false`, `schedule_probe=false`, and `recovery_walk_first=false`; comparator provenance is `verified`. The native inputs are the historical `/tmp/byakuya-matrix-godot-r11-ddfce1` files and are recorded with SHA-256 in `manifest.json`; this review does not relabel them as a current runtime hash. The prior r01 review remains as an audit of the pre-normalization failure and is not overwritten.
