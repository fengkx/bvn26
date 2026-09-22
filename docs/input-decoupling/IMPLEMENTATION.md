# Input delivery implementation

Implemented 2026-09-22 under the user's explicit implementation request.
This is the input-boundary phase of [ADR.md](ADR.md); networking, rollback and
external battle stepping remain deferred.

## Runtime boundary

- `godot/keyboard_input_source.gd` owns physical/logical keyboard polling and
  the configured ten-button mapping. `GameSession` retains its menu/settings
  helpers and delegates device reads to this adapter.
- `godot/match_input.gd` supplies both player slots. The live source can be a
  `Callable(slot, display_tick) -> Dictionary`; sparse live dictionaries use
  false for omitted buttons, matching the existing controller convention.
  A separate `intro_source(display_tick) -> bool` supplies the held skip request.
  Their defaults are the keyboard adapters. Neither callback runs in playback.
- `main.gd` reads intro input immediately before `BattleIntro.tick`, then reads
  both player samples at the existing point before actor advancement. `_input_for`
  now returns the delivered sample; it does not poll hardware. AI still returns
  an empty dictionary and follows its existing controller branch.
- `diagnostic_input_provider` remains a supported test source, sampled through
  this same boundary. Playback overrides it. Random/clock consumers, source
  callbacks, timers, collision and presentation scheduling are unchanged.
- `deliver_match_control` accepts normalized `confirm/up/down` press/release and
  `back` mouse press/release with an `inside` hit-test result. The pause menu
  interprets these through its existing source rules. Intro/KO/dead gates apply
  before delivery. Live control events execute synchronously, including title
  exit; they are not postponed until the next physics callback.

Control events occur between existing display updates. Their array order and
last completed `tick` retain multiple press/release events in the same interval.
Playback drains them before the next pause-menu/scene update, or before a manual
`_advance_fight` call. A rejected recorded control stops playback explicitly.
The pause-menu display timeline keeps advancing while fighters are paused.

`held`, `pressed` and `released` are sample-to-sample edges; the source fighter
controller still consumes held values. A down/up pulse wholly between samples
is not promoted into a new fighter input buffer. The pause menu uses separate
ordered events precisely because its source code handles those pulses.

## Developer recording and playback

From the repository root, with the project's Godot 4.7.2 binary:

```sh
/path/to/Godot --path godot -s res://tests/input_recording_runner.gd -- record /tmp/match-input.json
/path/to/Godot --path godot -s res://tests/input_recording_runner.gd -- replay /tmp/match-input.json
```

For recording, select mode, fighters, helpers and stage normally. Capture starts
when the fresh match is initialized, before the opening. Exit through the battle
menu's Title item, or complete the match until it leaves for character selection.
The complete document is written at exit (`MATCH_INPUT_SAVED`). Closing the
application midway does not create a complete recording. There is no replay UI.

Programmatic entry points on a fresh `main.tscn`:

- `arm_input_recording(path)` before entering the match.
- `start_input_playback(parsed_document)` restores both fighter/helper resource
  identities, stage, mode, life, difficulty and time settings before opening.
- An armed recording and playback are mutually exclusive. Starting playback
  while recording is armed returns an error before changing the scene or setup;
  the pending recording remains usable. Use a fresh scene to choose playback
  instead. Arming a recording during playback is also rejected.
- Both return a nonempty error string when initialization is rejected. Playback
  requires a fresh scene; arbitrary mid-match restoration is unsupported.
- Do not install additional logical producers during playback. Live gameplay
  keys, pause keys and mouse events are ignored while recorded input is active.
  Playback does not synthesize or clear global Godot keyboard state.

The format is `kind: match-input`, `format: bvn-match-input`, `version: 1`.
[Its schema](../../spec/schemas/match-input.schema.json) is separate from the
retained `replay.schema.json`. The [synthetic example](../../spec/examples/match-input.synthetic.json)
illustrates structure only, not an original-playback or legal gameplay trace.

Events are ordered `intro` and `players` samples for each display tick, with
`control` events between ticks and one explicit `end`. Every player sample has
all ten Boolean buttons in each of `held/pressed/released`. Loading rejects
unsupported versions, incomplete files, missing slots/buttons, inconsistent
edges, missing/duplicate/reordered samples, invalid setup/resources and unknown
operations. Runtime consumption checks the expected phase and tick; it stops
on divergence/exhaustion without polling a live input source.

Use recordings with the same runtime/content checkout. The format and engine
version are checked; the format is not a cross-build compatibility promise.
It records supplied input, not the random/clock tapes or asynchronous callbacks.
Uncontrolled live outcomes, especially AI/KO timing, need not reproduce; if a
recorded control becomes ineligible, playback reports the mismatch. Exact battle
state comparisons require separately controlled random, clock and callback
fixtures, as in `match_input_scene_smoke.gd`.

## Verification

See [the source audit and measured results](../../evidence/input-decoupling/README.md).
The existing original-reference fixtures retain their expected values. Their
input adapter now supplies logical P1 values directly; separate keyboard tests
cover remapping and physical device isolation. Existing `_input_for` assertions
were moved after the real update that consumes input, without changing their
expected held values or gameplay assertions.
