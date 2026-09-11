# Renji base-form source audit

This is the source and generated-data audit for the selectable base-form fighter
恋次 (阿散井·恋次). It is an intermediate import artifact; it is not an
original-player parity pass.

## Identity and range

The original catalog entry is `恋次` → `game/fighter/Renji.swf`, with helper
`石田`. `scripts/main.json` defines no `WKframe` clone for this entry, so only
form frame 1 is selectable. The retained SWF SHA-256 is
`7505e9591f46ba1d05bb03fff9450d52583804022a08ba3bb7a0ecfb21cb116a`.
The base-form root timeline is `DefineSprite_717`, with 1192 declared frames.

The extracted source labels are:

| Group | Labels and source frame spans |
| --- | --- |
| Movement | `站立` 1–9; `走` 10–19; `瞬步` 20–39; `跳` 40–55; `落` 56–71; `跳2` 72–88; `落2` 89–114; `落地` 115–126 |
| Ground combo | `砍1` 173–191; `砍2` 192–214; `砍3` 215–244 |
| Special | `必杀` 502–585; `上必杀` 586–676; `超必杀` 677–882; `招换` 883–944 |
| Hurt/defence | `防御` 945; `防御2` 946–956; `防住` 957–968; `被打` 969–981; `击飞` 982–993; `击落地` 994–1032; `起身` 1033–1052 |

The ranges are read from `data/slices/Renji-base.json`, which in turn reads
the SWF labels rather than guessing action lengths.

## SOURCE_FIRST five questions

1. The complete relevant frame scripts and callbacks are retained in
   `scripts/fighter/Renji.json` and indexed in `data/slices/Renji-base.json`.
   Root actions include the state writes at 128/144/174/193/216/246/311/347/
   384/454/482/503/550/587/643/678/864/946/958/970/979/982/983/994/1008,
   and the child `enterFrame` callbacks at 21, 30, 42, 50, 56, 72, 83, 89,
   116, 127, 173, 179, 194, 198, 217, 227, 249, 329, 361, 484, 540,
   626, 834, 946, 957, 960, 962, 971, 972 and 984. Empty frames remain in
   `timeline.json`; no end label is treated as an implicit return to standing.
2. The source uses both new `PlaceObject2` and `MOVE`. The hurt callback is
   placed at `DefineSprite_717/frame_971/PlaceObject2_16_28/...`; jump motion
   is placed at `frame_42/PlaceObject2_16_31/...`. The generated timeline keeps
   `move`, `placed_frame`, and clip actions, so a new instance does not inherit
   the previous instance state and its callback begins on the following root
   frame.
3. Explicit exits are compiled from source `gotoAndStop`/`gotoAndPlay`,
   `stop()`, and conditional gotos. Examples are `frame_189` (`砍1` → `站立`),
   `frame_241` (`砍2` → `站立`), `frame_274` (`砍3` → `站立`), `frame_539`
   (`bsd` end), and `frame_1024` (`击落地` → `站立`). Any frame without a
   terminal script remains timeline-driven; it is represented in the compiled
   action data rather than replaced by a generic finish hook.
4. Regression assertions target source invariants: Sprite 717 identity and
   hash, exact source spans, the `hits = 0` reset at frame 2, `onBeHit()` at
   970 and `onBeHit(true)` at 983, source super presentation frames, and the
   source callback paths. No guessed hitbox, height, delay, or damage value is
   introduced.
5. The original player produced complete 360-frame same-input traces for the
   neutral `砍1` case and the ten-case high-risk subset. The latter's summary
   is `original-high-risk-r02.json`; all ten comparisons are currently
   matched, including air, jump, three supers, summon, and defence boundaries.
   The remaining 44 original captures were collected in
   `/tmp/bvn-renji-original-rest-r01`; the first batch had 36 matches, seven
   runtime-timing differences, and one shared-helper parse failure. Reusing those
   captures after the shared runtime stabilized made all eight cases match
   722/722. The merged candidate audit is `original-parity-audit-r03.json`; a
   final single-hash native rerun is recorded in
   `/tmp/renji-native-freeze-final-r02/compare-summary.json`; all 54 cases
   matched 722/722 state rows under the frozen runtime hashes.

## Generated artifacts

The source-derived slice is in `data/slices/Renji-base.json` and
`data/slices/Renji-base.timeline.json`; the combat model is
`data/actions/Renji-base.json`. Materialized runtime assets and generated
controllers are under `godot/generated/fighters/renji/`. The complete retained
base-form action fixture is `evidence/combat/renji-base/source-fixture.json`;
the focused source regression is `tools/tests/test_renji_import.py`.

## Validation status

The import pipeline completed with 348 materialized assets and generated player
and CPU controller data. After the shared envelope compiler repair, Renji's
sound bake completed with 34 frames; frame 21 sound 38 retains the authored
dynamic envelope and produces segment SHA-256
`fb6428b8943be50db60d2951bb67d304b59ef0ce08b97c0460ed856804ddac4e`.
Native import smoke, the expanded six-fighter/three-helper selection smoke,
and the 54-case production matrix pass on Godot 4.7.2; the matrix summary is
`native-matrix-r01.json`. The Web package exports and boots in the local
Chromium browser, and r02 real-input selection checks show new fighter
portraits/footers plus helper 鼬; full browser combat/pause/return/reselect is
still outside this evidence. The original-player audit now has 54/54 candidate matches (ten high-risk
cases plus 44 remaining held/mirror/neutral cases); eight old differences were
resolved by reusing their captures after the shared runtime stabilized. The
abandoned mixed-hash native rerun is excluded. The final 54-case run with explicit per-fixture helper configuration is
recorded in `native-freeze-explicit-helper-r05.json`; all 54 cases matched
722/722, and its five runtime hashes agree before and after the run. The prior
r04 record is retained as historical diagnostic evidence. Browser combat and
audiovisual parity are also pending.

The dedicated audiovisual probe records source `StartSound` events and runtime
playback for six representative frames: movement frame 21 sound 38, combo
frame 177 sound 60, `必杀` frame 516 sound 69, `上必杀` frame 606 sound 386,
and `超必杀` frames 689/832 sounds 446/504. Each fires once and resolves to
the generated segment's authored sample range and hash. The native trace is
`/tmp/renji-audiovisual-r01/runtime-audio-trace.json`; the formal audit is
`audiovisual-audit-r01.json`. The temporary Web probe at `127.0.0.1:8061`
was observed through CUA at all six frames (visual observations are recorded
in the audit, but the CUA tool provides no persistent screenshot path).
Headless Godot has no viewport texture, and original-player same-stage
captures remain pending, so no pixel identity is claimed.
