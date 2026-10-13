# Training P2 input investigation (2026-10-13)

A concrete Web input defect was reproduced on production commit
`f8d22f3a42ce9931dde2714725695b75791915c9`: press P2 NumPad3 on the canvas,
focus the export-log toolbar button, release NumPad3 there, then focus the
canvas again. P2 continues receiving `dash=true` and repeatedly enters 瞬步.
The player input source is active and `p2cpu=false`. This requires a prior
keypress; it does not establish the cause of an entirely untouched fresh
session, which remained idle with both the default roster and P2 Itachi.

## Original Flash behavior and source gate

Line numbers below refer to the embedded `path` in the JSON script bundle;
`source-excerpts.json` preserves the cited text.

- `scripts/main.json`, `DefineSprite_603/frame_15/DoAction.as:1-5`:
  training sets mode 4 and both CPU flags false.
- `scripts/main.json`, `frame_8/DoAction.as:661-688`: `chushi` assigns P2
  keyboard controls, including NumPad3 for 冲 (line 684). Training is a
  keyboard-controlled player, not a frozen dummy.
- `scripts/fighter/itachi.json`, `DefineSprite_294/frame_1/DoAction.as:442-461`:
  player `initCtrl` unloads AImain; only AI registers `randAI`.
- Same bundle, `DefineSprite_11/frame_1/DoAction.as:369-390`: player `rush`
  requires held 冲 without 上/下. Repeating a held command is source behavior.
- Same bundle, `DefineSprite_294/frame_1/DoAction.as:685-808`: directional
  dash requires the relevant input/AI conditions; `onDashing` terminates,
  clears `dashing`, and explicitly returns to standing or falling.
- `scripts/main.json`, `DefineSprite_1991/frame_1/DoAction.as:86-101,137-139`:
  training recovers health/energy every 1000 ms when `beida == 0`, without
  moving either fighter.

Source-first five questions for the affected input boundary:

1. No character frame program is changed. For Itachi 瞬步 (22-37), frame 23
   calls `shunbuxg`; frame 33 explicitly goes to 站立 and plays. Other frames
   in that interval have no DoAction. The frame-24 controller enterFrame
   moves by speed*3 while running and checks super inputs; frame-31 damage
   receiver enterFrame calls `beida`. Exact scripts are in the excerpts.
2. Those callbacks belong to the source PlaceObject paths at frames 24 and
   31. This patch changes no placements, MOVE lifetimes, or clip variables.
3. Frame 33 uses explicit goto/play, not a guessed label-end transition.
   Directional dash has its separate explicit exit at body lines 791-806.
4. The invariant is released player keys must not remain held. P2 keyboard
   control and held-command behavior remain intact. Web focus handling is
   the platform requirement in SPEC FR-10 / VALIDATION AT-13.
5. A fresh native Flash Player Debugger capture using
   `tools/probes/capture_native_player.py` ran the existing training fixture
   with Naruto/Itachi for 300 frames: movement, attacks, directional dashes,
   supers, summons and recorded training timer callbacks. The native Godot
   replay matches **602/602 actor states exactly**, zero differences.
   This is a gameplay comparison, not a claim that standalone Flash has
   the HTML toolbar focus lifecycle.

## Root cause and fix

The deployed Godot Web engine registers keydown/keyup on the canvas.
Moving focus to another element in the same document sends canvas blur,
but does not send window blur. The engine's window-blur key reset therefore
cannot handle this sequence, and the keyup on the toolbar misses the canvas.
`KeyboardInputSource` keeps polling Godot's stale key state each frame.

`RenderSurface` now remembers key events delivered to the game and sends
matching releases on its Window focus-exited signal (canvas blur on Web).
Both physical and logical key identities are preserved. Fresh presses after
refocusing still work. No character, AI, shared combat scheduler, key map,
or original input predicate is changed.

`web-focus-before.json.gz` records the production failure: at tick 664,
P2 has received 160 retained ticks of held dash and repeated player-origin
standing/瞬步 transitions despite the key being released on the toolbar.
`web-focus-manual-release.json.gz` shows that sending the missing keyup to
the canvas clears the stale input without any combat-state repair.

## Other hypotheses checked

- Default P1/P2 key maps are disjoint. Every default P1 key was injected
  separately; none activated P2. Gamepad axis/button on device 1 and touch
  events did not activate keyboard inputs. Production has no adapter
  mapping those events to P2 keys.
- Custom saved overlapping bindings can intentionally control both players;
  an injected P1 attack with P2 dash bound to that key demonstrated this.
  Flash also assigns configured keys directly. No binding was rewritten.
- IME text with no physical/logical key does not activate P2. The physical
  OR logical polling may overlap custom letter bindings under alternate
  layouts; this needs a relevant keypress and does not manufacture idle input.
- P1 movement/attack/dash, a real AI interval firing before VS COM→training,
  nextfight, reselect, and a single P2 dash followed by release were checked
  headlessly. Itachi and Naruto settled normally; AI flags/intervals cleared.
  `training_input_probe.gd` and `training_keymap_probe.gd` preserve the probes.

## Verification boundary

- Existing shared PvP/training comparisons: 602/602 each, no tolerance change.
- `shared_mode_lifecycle_smoke.gd`: passed again after the input fix.
- `input_focus_smoke.gd`: both players release on focus loss; fresh P2 press works.
- Targeted production and local-pack Chromium runs use independently launched
  headless browsers, never the user's Chrome/profile.
- Local PCK export reuses the production engine/shell for the Web comparison;
  its embedded build metadata is unknown, so the pack SHA is recorded separately.
- Complete browser/platform and character parity remain pending. No production
  deployment is part of this change.

The fixed browser run recorded 8 genuinely held P2 dash samples, then false
through tick 3484 after the first toolbar-release sequence. A separate long
hold stayed true through tick 3991; after releasing on the toolbar again,
the last 100 samples through tick 4663 were all false. See
`web-focus-after.json.gz`, `web-focus-held.json.gz`, and
`web-focus-released.json.gz`; pack/source hashes are in `report.json`.
