# Five selectable source forms

This delivery fills the five remaining original selection cards: Hitsugaya Bankai,
Rukia Shikai, Ichigo Bankai, Naruto One Tail and Curse Mark Sasuke. The enabled
catalog now contains all 40 original fighter cards and six assists. It connects
existing source-compiled form packages to selection, original portraits/footer,
opening, offline modes and friend-room host authority.

## Source-first answers

1. `scripts/main.json`, `DefineSprite_1900/frame_5/DoAction.as` loads both base
   wrappers, selects each `WKframe` in P1/P2 order, then initializes controls.
   `source-first.json.gz` retains that source and all five BODY/init source sets.
   Each selected form's existing `ai.json` contains its compiled per-frame calls.
2. Parent frame 2 places a fresh BODY, with the source matrix and instance load
   values from its already-reviewed form graph. We reuse those packages without
   changing geometry or attack rules. With only P1 selected as a form, its BODY
   is newer than retained base P2; callbacks must preserve that registration order.
3. Action exits and timeline fallthroughs remain the compiled `combat.json` and
   `timeline.json` rules. The new `intro.json` files are compiled from the selected
   BODY's original opening labels and scripts. The intro-generator run's unrelated
   historical output drift was excluded; only the five new form records were
   added. Existing opening records and main presentation assets are unchanged.
4. Direct selection starts a fresh wrapper with `万解=false`: source `doWanKai`
   runs `initCtrl` without a transformation energy cost or inherited drain timer.
   CPU initialization creates one source `airanset`, with no duplicate legacy
   random timer. The full base form graph remains available for later transitions.
5. Ten task-only original Flash captures and the exact native input replays match
   all 8,420 actor states on 14 fields, without tolerances. Each form has a combo
   and two successful super entries. These fixtures do not claim opposite-facing
   coverage. `cases/`, `comparisons.json` and `source-native-raw.tar.gz` bind inputs,
   source instrumentation and native results. The preliminary Rifagu mismatch
   (energy at ticks 14/26) is retained: fixing source BODY registration order made
   the same input match. No source baseline was edited.

## Integration checks

`selected_form_flow_smoke.gd` verifies both player slots for all five forms:
selection, natural opening, attack, checkpoint replay and next round. It also
checks fresh CPU initialization and the single source timer. Five paired-form
host-authority projection tests pass. Native headed screenshots were inspected:
all five selectable cards, portraits/footer, HUD and active form attacks render.
The original base player controller, player visual smoke and Ichigo form graph
checks pass; their sandbox macOS certificate-query warning is retained in logs.
32 backend tests and source registry/intro/form guard tests pass. The initial
backend catalog test caught helper ordering drift; the service now matches the
menu's exact order. Initial temporary harness argument/index mistakes are retained
alongside the corrected runs. Timings in `summary.json` are measured process time.

Full audiovisual equality and whole-project M6 acceptance remain separate tracked
work; these checks deliver the five selectable forms without changing those flags.

The friend-room backend catalog was deployed as
`444b827a-551c-4d1b-94f3-e0eac227a68f`. The live probe created a room
(default host authority, map unconfirmed), selected all five forms successfully,
received TURN credentials and closed the room. `live-service.json` records the
redacted results; no credentials or room tokens are retained.

Standard Web export, its lobby/compatibility checks and isolated Chromium WebGL
boot pass. The executed PCK contains all 40 cards, six helpers and the five forms
with portraits, openings and compiled controllers. The first packed probe used
FileAccess for an exported script; the corrected probe uses ResourceLoader to
follow Godot script remaps. Both logs are retained. `web/build-metadata.json`
records the build snapshot and PCK hash; generated UID/import sidecars explain
its dirty snapshot status. Frontend production deployment is tracked separately.
