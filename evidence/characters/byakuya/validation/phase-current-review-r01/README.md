# Byakuya phase-current independent review r01

This review audited the first three `boundary-r11-current-missing5` IDs against the retained source index and `/tmp`/`/private/tmp` candidates. The source/build paths are present in the workspace:

- `byakuya-123-airhit-neutral`: `evidence/characters/byakuya/native-capture-airhit-r05/events.jsonl.gz` + `build.json`
- `byakuya-139-airMagichit-neutral`: `evidence/characters/byakuya/native-capture-air-special-r05/events.jsonl.gz` + `build.json`
- `byakuya-849-defence-neutral`: `evidence/characters/byakuya/native-capture-defence-r05/events.jsonl.gz` + `build.json`

The retained files are AIREF pipe records (`AIREF|...`), not the JSONL state-event format consumed by `tools/probes/compare_mode_reference.py`. Running the strict comparator for all three therefore fails at `json.loads` on the first line with `JSONDecodeError`; no new 0-difference result is claimed. The corresponding current native files and SHA-256 values, plus the exact failed input boundary, are recorded in `review.json`.

`/private/tmp/byakuya-matrix-capture-r04` contains other 123 airhit scenarios (`air_target`, `guard`, `held`, etc.) but no neutral 123 source directory, and no 139-neutral or 849-neutral source directory. The historical r11/r11b manifests remain untouched; their matched rows lack comparator-compatible source provenance and are not re-promoted by this review.
