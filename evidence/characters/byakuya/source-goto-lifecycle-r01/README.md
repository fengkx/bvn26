# Byakuya source goto lifecycle audit r01

This is a bounded, read-only audit for base-form Byakuya. It does not claim full parity and does not modify `game/`, `scripts/`, or production runtime.

## Source sequence

The selected lifecycle is `站立 (A) -> 招换 (B) -> 站立 (A)`. Locked source evidence is `game/fighter/Byakuya.swf` plus `scripts/fighter/Byakuya.json`: sprite 631 frame 819 runs `doZhaoHuan()`, and frame 844 runs `gotoAndStop("站立"); play();`. The generated timeline is recorded only as a contract projection; it is not treated as locked source evidence.

## What is established

The current code carries an entry serial through frame rendering, only coalesces identical consecutive pending gotos, assigns a new generation to a same-depth placement after a new entry serial, and gates callbacks with `placed_tick < display_tick`. Local child state stores its own start frame, age, playing flag, and source variables. The existing `nested_start_sound_smoke.gd` passed with exit code 0 and covers synthetic same-depth replacement/redraw behavior.

## What remains unaccepted

The available Byakuya 819 native freeze is a single B-entry observation. The current Godot 819 metadata has no child-frame map and is not bound to the current runtime hash. There is no paired original-player/Godot A→B→A trace, so same-frame re-entry and child-clock parity remain pending.

## Minimal next probe

Run one explicit `站立 -> 招换 -> 站立` fixture with identical input, clock, helper, and initial state on both sides. Record every display tick with source frame, entry serial, pending/defer state, frame-script serial, depth/character/placed-frame, generation, placed tick, child local frame/age/playing, and callback dispatch order. Reject empty child maps, placement-tick callbacks, collapsed A→B→A generations, missing hashes, or missing locked source events.

See `audit.json` for file hashes, line-scoped runtime invariants, existing observations, and the acceptance boundary.

## Executable analysis probe

The analysis-only builder is `tools/probes/byakuya_source_goto_lifecycle.py`. It verifies the locked SWF/script hash binding, extracts the exact 631/8, 819, and 844 source entries, extracts the source sequence and writes a native capture contract; it does not emit preset lifecycle results:

```sh
python3 tools/probes/byakuya_source_goto_lifecycle.py \
  --run-id byakuya-goto-r01-20260921 \
  --output evidence/characters/byakuya/source-goto-lifecycle-r01/probe-r01.json
```

`probe-r01.json` is intentionally `analysis_only_not_parity`. It contains source facts and capture requirements only; it does not contain preset generation or entry-serial results. Native capture still requires the global Flash lock and a clean, source-backed input fixture. The native command template and fail-closed fields are embedded in the JSON.

## Real Godot runtime experiment

`godot/tests/byakuya_source_goto_lifecycle_probe.gd` was executed with Godot 4.7.2. It instantiated the real `FighterRuntime` for `res://generated/fighters/byakuya`, called `source_goto_label` for `站立 -> 招换 -> 站立`, then called the same `招换` entry twice. The result is [godot-runtime-r01.json](godot-runtime-r01.json), status `executed_analysis_only`. It records eight real runtime rows and confirms only the observed same-frame entry serial increase; it does not assert a generation value or native parity. The action label remains `站立` during this direct source-goto experiment because frame scripts, rather than the probe, own the action transition.

## Real Godot main-scene / registry observation

`godot/tests/byakuya_source_goto_main_probe.gd` was executed against the real
`main.tscn` bootstrap with the Soul/Soul fixture. It reaches Ready at physics
tick 276, injects one deferred `source_goto_label("招换")`, and records the
real `SourceCallbackRegistry` across eight advances. The output is
`godot-main-r01.json` (exit code 0): source frames 814 through 821 and the
frame-script serial are observed through the real main loop. This proves
main-scene scheduling through frame 819, but does not execute a matching
A→B→A sequence; the child map is empty, so child lifetime remains unaccepted.

## Isolated AVM build

`tools/probes/build_byakuya_source_goto_probe.py` built `/private/tmp/byakuya-avm-goto-r02` with a copied `main.swf`, copied fighter assets, and a compiled temporary `game/fighter/Byakuya.swf`. The patch observes frame 819 child identity and performs a synchronous, behavior-changing `gotoAndStop("站立") -> gotoAndStop("招换") -> gotoAndStop("站立")`. The compiled frame-819 script was re-exported and checked for the observer. Provenance is archived under `avm-goto-r02/`; the build remains `built_not_run` and is not role parity evidence. Any Flash run must use the global capture lock and preserve raw `AIREF` events.

## Current 819 GUI capture

`evidence/characters/byakuya/audiovisual-r06/godot-819-gui-r01/` is a current-code GUI run of the same Byakuya/Ic​higo Soul/Soul fixture. It reached action `招换`, source frame 819, relative fight tick 15, energy 200, and records an empty `visual_child_frames` map. It is paired to r29 by fixture and target metadata only; child lifecycle remains open.

## Native controlled AVM capture r06

`avm-goto-r06/` is a normal `build_ai_reference.py` battle-bootstrap build
with a read-only observer added to the locked frame-819 DoAction. Its native
capture completed with exit code 0, 5397 events, and a `done` marker. The
observer recorded the controlled synchronous sequence `819 -> 1 -> 814` at
display tick 466, then a controlled cross-display sequence at ticks 467--469.
Raw events, build, fixture, and environment are archived under `avm-goto-r06/`;
`native-context-r01.json` records nearby native state and helper rows. This is
a behavior-changing AVM experiment, not natural-input parity. The observer
records paths and frames, but not `object ===` identity or per-instance
sentinels, so child generation/lifetime remains unproven.

## Paired observation boundary

`paired-observation-r01.json` binds the native r06 capture to the real Godot
main-scene output. Both sides have executable scheduling evidence, but their
controlled sequences are not identical: native executes the injected
same-callback and cross-display A→B→A observer, while Godot executes one
deferred entry and reaches frame 819 through the real registry. Same-frame
re-entry, child identity, and natural-input parity therefore remain
fail-closed.

`paired-observation-r02.json` is the completed controlled identity run. Native
r09 uses the normal battle bootstrap and records `mian`, `jiao`, and `bdmn`
reference equality plus a per-step sentinel across same-callback A→B→A,
repeated B→B, and cross-display A→B→A. The capture has 5247 events and a
`done` marker. The matching Godot main probe is `godot-main-r02.json`; it
records each label call, entry serial, pending frame-script queue, registry
size, and three cross-display advances. Godot has no equivalent AVM object
reference and its child map is empty, so this closes the controlled observation
of the native references but does not establish child-generation or natural
input parity.
