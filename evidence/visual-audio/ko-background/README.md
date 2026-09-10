# KO background child timeline repair

The persistent red square was source Shape 1507, held on Sprite 1509 frame 1.
The parent blackMu (Sprite 1510) correctly stopped at its `KO` label, frame 5,
but the generic renderer derived the unnamed child's frame from the stationary
parent frame. It therefore never enlarged or flashed the authored background.

## Source-first evidence

- Source: locked `game/main.swf`, SHA-256
  `707fac0ec6bb2af1a3d18dc308dd403cb556a0988144b0f6f10555382287f92d`.
- `scripts/main.json`: `DefineSprite_1510/frame_1/DoAction.as` and
  `DefineSprite_1509/frame_30/DoAction.as` contain `stop();`. These are the only
  scripts in the graph. Sprite 1509 frames 1–29 have no frame script.
- `godot/generated/main/blackMu/timeline.json`: parent frame 5 newly places
  Sprite 1509 at depth 1; parent frame 1 removes it. Its red Shape 1507 grows
  through retained placements, followed by full-screen color frames. Parent
  `gotoAndStop("KO")` does not stop the child; the child's own frame-30 script does.
- `tools/probes/build_ko_background_probe.py` copies source definitions
  535, 591 and 1507–1510 byte-for-byte into a separate SWF. The only injected
  script attaches the background, selects `KO`, and samples both playheads.
  Native Flash Player 32 yields parent 5 throughout, child 1 through 30, then
  child 30 through sample 35. See `native.log` and `comparison.json`.
- This is an isolated original-symbol probe, not an original full-match or
  browser visual-parity claim. The full-match reproduction uses Godot only.

## Implementation and validation

`compile_display_timeline.py` compiles both stop scripts with their source
paths/hashes, rejecting unaudited scripts. `ScriptedTimelinePreview` reuses
`KoTimeline` to advance children independently, preserve them during repeated
parent synchronization, execute their stop script and restart after removal.
Only BlackMu selects this renderer. Main advances it once per fight display
tick, including fighter KO pause, before new placements created by that tick.

The initial regression failed with `tick 1, frame 1`. The repaired integration
fixture matches all 36 original playhead samples, also checking KO pause,
repeated rendering, final stop and a fresh KO placement. KO rendering, both
winning sides/two rounds, player controller and running visuals pass focused
native checks. The Godot 4.7.2 Compatibility window now shows the full-screen
red flash at sample 10, where the same probe previously showed a 33-pixel red
square in the 900x600 window. Temporary screenshots are in `/tmp/ko-probe-*.png`.

Rebuild and test:

```sh
python3 tools/importer/compile_display_timeline.py godot/generated/main/blackMu
/path/to/Godot --headless --path godot --script res://tests/ko_background_smoke.gd
python3 tools/probes/build_ko_background_probe.py --ffdec /path/to/ffdec.jar \
  --output /tmp/ko-background-new-run --run-id ko-background-new-run
python3 tools/probes/capture_native_player.py /tmp/ko-background-new-run \
  /tmp/ko-background-new-run/native.log --allow-window-activation
```

Scope: this fixes the frozen background animation. Original whole-match
presentation timing and browser acceptance remain pending. No milestone was
marked complete; elapsed effort is not estimated from artifact count.

The shared-mode replay also passes: 602 original actor states each for PvP
and training. `check_handoff.py` and `git diff --check` pass. `verify.py` was
run after updating this change's tracked hashes; it remains blocked by 11
hash mismatches in concurrent AI/receiver/effect-tool changes, outside this
repair. Locked `game/` and `scripts/` inputs report no mismatches. Web export
and browser execution were not repeated for this repair.
