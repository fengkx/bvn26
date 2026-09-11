# Kakashi native matrix and original capture plan r01

The native matrix contains 21 cases. The planned original capture batch contains the
15 target-positive cases, four source-valid energy negatives, and one explicit
super no-hit case. The two scope exclusions (`bishaAir` and `wankai`) are not
sent to Flash. Native execution is complete; original Flash capture remains
pending the shared-player slot. This record keeps execution separate from
same-input parity.

An attempted batch was started before an explicit shared-window grant and
overlapped another agent's Flash session. Every capture produced by that
attempt is invalid for acceptance, including files whose provisional compare
reported `matched`; the logs and builds are retained for audit and must be
replayed after a clean window grant.

Invalid attempt files: `kakashi-129-airhit-air_target`,
`kakashi-156-airMagichit-air_target`, `kakashi-193-nornalhit-dash_twice`,
`kakashi-193-nornalhit-mirror`, `kakashi-193-nornalhit-neutral`,
`kakashi-22-rush-dash_twice`, `kakashi-22-rush-neutral`, and
`kakashi-301-skill1-guard` under `/tmp/bvn-kakashi-original-matrix-r01/`.

- Source: `卡卡西` / `Sprite710`; SWF SHA256:
  `48587becee990fccfd7450a1b605a24b2d654dbd15569857659f67346bddb2fc`.
- Native command used:
  `python3 tools/test_move_cases.py --godot /tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --cases /tmp/kakashi-case-inputs-final --output /tmp/kakashi-native-matrix-final --jobs 1`
- Result: 21/21 executed, complete 602 states each, 15/21 source target windows seen; no script errors.
- Original batch manifest: `/tmp/kakashi-original-cases-r01/paths.txt` (20 cases: 15 positive, 4 energy negatives, 1 super no-hit).
- Machine-readable result: `evidence/characters/kakashi/native-matrix-r01.json`.

The six target misses are source-valid negatives or scope exclusions:

- Energy negatives: `kakashi-1030-zhaoHuan-energy_below` (ql=99),
  `kakashi-689-bisha-energy_below` (ql=99),
  `kakashi-757-bishaUP-energy_below` (ql=99), and
  `kakashi-863-bishaSuper-energy_below` (ql=299). Each has an authored
  dispatch but the source resource gate rejects the input.
- Source no-op: `kakashi-missing-bishaAir-air_target` declares
  `has_source_timeline=false` and `target_frames=[null,null]`; its controller
  dispatch has no base-form timeline label to enter.
- User-deferred form: `kakashi-missing-wankai-energy_below` likewise has no
  source timeline or target window; the transformed-form entry is outside this
  base-form task and is not sampled.

## Complete original/native comparison command

Run this exact batch only after the shared Flash window is explicitly granted.
It uses
one isolated build/capture directory per case, preserves the original logs,
and then compares the collected original events to the production replay:

```zsh
FFDEC=/private/tmp/bvn-ffdec-26.2.1/ffdec-cli.jar
GODOT=/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot
ROOT=/Users/fengkx/me/code/bvn2_6
CASES=/tmp/kakashi-cases-matrix-r01/paths.txt
OUT=/tmp/bvn-kakashi-original-matrix-r01
mkdir -p "$OUT/cases"
while IFS= read -r case_file; do
  [[ -z "$case_file" ]] && continue
  id=$(basename "$case_file" .json)
  build="$OUT/build-$id"; capture="$OUT/$id.original.log"; collected="$OUT/$id.collected"
  normalized="$OUT/cases/$id.json"; native="$OUT/$id.native.json"; compare="$OUT/$id.compare.json"
  frames=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["frames"])' "$case_file")
  cp "$case_file" "$normalized"
  python3 "$ROOT/tools/probes/build_ai_reference.py" --ffdec "$FFDEC" --output "$build" --run-id "kakashi-r01-$id" --frames "$frames" --p1-character 卡卡西 --p2-character 一护 --move-case "$normalized" --dynamic-move-case
  python3 "$ROOT/tools/probes/capture_native_player.py" "$build" "$capture" --timeout 120 --allow-window-activation
  python3 "$ROOT/tools/probes/collect_ai_reference.py" --build "$build" --capture "$capture" --output "$collected"
  "$GODOT" --headless --path "$ROOT/godot" -s res://tests/move_case_reference.gd -- "$normalized" "$native"
  python3 "$ROOT/tools/probes/compare_mode_reference.py" "$collected/events.jsonl" "$native" --output "$compare"
done < "$CASES"
```

The authoritative native case order is `/tmp/kakashi-cases-matrix-r01/paths.txt`;
the copied exact inputs used for native execution are under
`/tmp/kakashi-case-inputs-final/`. The original capture subset and super
no-hit path are listed in `/tmp/kakashi-original-cases-r01/paths.txt`.
