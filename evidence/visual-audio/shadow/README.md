# Source shadow snapshots

## Source-first gate

1. All 35 fighter wrappers have the identical `frame_1/DoAction.as::showdow`.
   `++_si > 1` resets the wrapper counter and returns; other calls invoke
   main `frame_8/DoAction.as::shadowEffect` with alphaStart=100/alphaLose=10.
   The complete functions and source hashes are retained in generated/main/shadow.json.
   BODY onDashing calls showdow with RGB offsets 20/-100/255 after movement.
2. shadowEffect creates a new BitmapData using truncated wrapper width/height,
   draws the local bounds translated to the origin, and attaches a new clip in
   lyr_plr_bkeft (depth 5 on all ten imported stages). It copies X scale and
   applies the signed bounds offset. It is a frozen snapshot, not an animated clone.
   New onEnterFrame registrations begin on the next display tick.
3. There is no label transition or animation in a shadow. Its callback subtracts
   alphaLose and removes itself at alpha <= 0. It has no zhanting guard.
4. Counter lifetime is the outer fighter wrapper, not an action. Independent
   snapshots retain their position, pose and color; no input, attacks, sounds or
   randomness are duplicated. Source alpha writes quantize to signed 1/256 units.
5. Native original Flash `shadow-down-r02` exercised the existing two-window
   down+L input fixture, retaining showdow and shadowEffect unchanged except
   read-only logging. It observed nine spawns across two dashes at ticks
   13/15/17/19/21/29/31/33/35. Fade starts on the next tick, with alpha
   89.84375,79.6875,69.53125,59.375,49.21875,39.0625,28.90625,18.75,
   8.59375,-1.171875, then removal. Native log/build/diff are retained below.

Initial native red: the first showdow call only warns; no snapshot is created.
This initial failure is retained separately from the passing implementation below.

## Implementation and result

The shared service is now connected for both keyboard and CPU actors in all local
modes. `build_shadow_rules.py` validates complete audited function bodies across
35 fighter SWFs, compiles the source constants/layer and records the controller
lifetime rules. No character-name rendering branch was added.

`ShadowSnapshot` retains only Sprite2D/Polygon2D display nodes in a one-shot
transparent SubViewport. Its texture freezes the existing pose; no actor script,
input, collision, random draw or sound is copied. Tint is applied to the composite
bitmap using the source RGB offsets, then each instance fades through the shared
callback registry. Exiting combat disposes snapshots before registry teardown.

Original references now match **297 ordered events**: down/up player dashes and
mirrored CPU dashes, each with two input windows and 99 creation/fade observations.
Comparisons check exact source frame, placement, facing, bitmap dimensions, alpha,
creation order and callback order. The raw original logs/diffs are immutable gzip
artifacts; JSON rows only extract the explicitly logged fields.

The original `initCtrl` unloads player AImain but stops CPU AImain on frame 2.
This affects bitmap bounds even though the sensing boxes are invisible. The
independent native bounds probe confirms nearest-twip transformed edges; the
nested probe confirms concatenated translation quantization before shape bounds
(the aerial lower edge is -49.6, not -49.55). Shadow rendering uses this measured
geometry without modifying gameplay collision bounds or numeric tolerances.

## Validation

- Three-character/two-facing smoke: independent counters, counter continuity
  across actions, frozen pose/position/size, fading under gameplay pause, and
  cleanup with live snapshots at exit.
- Native graphical and Chromium WebGL: nonempty snapshot bitmap; byte-identical
  snapshot pixels after the source actor moves, changes pose and flips facing.
  `native.png`, `web.png`, `visual.log`, `web-log.json` retain the observations.
- Existing six direction-dash/Up+I references, player controller/visual tests,
  hurt-summon regression, PvP/training original comparisons and r13/r14/r15
  observed-field replays pass. See `regressions.json`, `ghost-regressions.log`
  and `shared-modes.log`.
- `before.log` retains the initial missing-service assertion. The native/macOS
  certificate warning is an environment warning, not a shadow mismatch.

Rebuild rules: `python3 tools/importer/build_shadow_rules.py`.
Run Godot tests `shadow_smoke.gd`, `shadow_reference.gd -- down|up OUTPUT.json`,
and `shadow_cpu_reference.gd -- super-dashx OUTPUT.json 681 3`.
Run `res://tests/shadow_visual.tscn` graphically for the texture-freeze check;
it writes screenshots under /tmp on native, and logs success in Web.

To reproduce original observations, use `build_ai_reference.py --shadow-probe`
with `--ghost-probe down|up --frames 80`, or `--dash-probe super-dashx
--dash-trigger-frame 681 --dash-duration 3 --frames 240`. Capture only the isolated
copy with `capture_native_player.py --allow-window-activation`.

This closes the missing snapshot service. It does not establish full original
pixel identity, arbitrary transformed poses, every character's shadow call site,
Firefox/Safari parity, or the deferred transformation mechanism. Native/Web
texture-freeze equality compares successive port snapshots, not Flash pixels.
The local production Web export is rebuilt; online deployment is not performed.
