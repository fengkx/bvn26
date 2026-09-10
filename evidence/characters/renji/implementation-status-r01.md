# Renji base-form implementation status

阿散井·恋次 (`恋次`) is imported from `game/fighter/Renji.swf`, form frame 1;
Bankai and transformation entries are outside this delivery. The source audit,
timeline geometry, combat model, 348 materialized assets, player/CPU aliases,
and 34-frame authored sound bake are retained under the generated/data paths
listed in `evidence/combat/renji-base/README.md`.

Validated on Godot 4.7.2:

- source/import regression: 19 Python tests and `RENJI_IMPORT_SMOKE_OK`;
- Vs Human/Vs Com selection and helper-driver smoke:
  `EXPANDED_SELECTION_SMOKE_OK`;
- 54 source-derived native move cases: 54/54 strict marker passes, with no
  script/resource/JSON/assertion errors; see `native-matrix-r01.json`;
- ten high-risk original-player 360-frame same-input comparisons are matched;
  see `evidence/combat/renji-base/original-high-risk-r02.json`; the remaining
  44 captures are now also collected. The merged candidate audit records 54/54
  matched after eight stable reruns in `original-parity-audit-r03.json`.

The frozen-hash 54-case native rerun completed with one hash set and 54/54
comparisons matched at 722/722 states; see
`/tmp/renji-native-freeze-final-r02/compare-summary.json`. Acceptance remains
pending browser audiovisual evidence and original-player pixel/audio checks;
this status does not claim full visual/audio parity.
