# Fresh Flash / Godot sample audit — 2026-10-19

Audited runtime: `2d3336bf039e7ad0ac92c22423273f664b432225`, branch
`audit/sample-new-chars`, worktree `/Users/fengkx/me/agent-code/bvn2_6-sample-new`.
The remote master was checked with `git ls-remote` and had the same SHA.
The stale main checkout was not used for edits, builds, replay or commits.

This audit records newly launched Adobe Flash Player captures and newly executed
Godot replays. It does not substitute old PR checks for new execution. Results,
per-case timestamps, fresh run IDs, trace hashes, counts and first divergences
are in `comparisons.json`. See `COORDINATOR_HANDOFF.md` for the final disposition.

## Method and evidence

- Adobe Flash Player Debugger 32.0.0.465, persistent installation at
  `/Users/fengkx/me/code/flash-player/Flash Player.app`. Binary SHA-256:
  `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
- Godot `4.7.2.stable.official.ed1daf0bf` from the requested toolchain.
- Three new dynamic probe builds use current locked inputs and the current
  `tools/probes/build_ai_reference.py`; exact instrumentation is retained.
  JPEXS version 26.2.1 is verified from the JAR project properties. The
  JPEXS JAR actually used has SHA-256
  `090ab695053ad94cba6408574c7d7eea20ec60b6ae789ee6056a23f45106762f`.
- All fights use mode 3, AI off, current-world stage, the audited fighter as P1,
  Ichigo as P2, explicit Gaara/Kon helpers, controlled initial X/energy and
  240 fight ticks. Each complete comparison contains 482 fighter states.
- Flash launches are serialized through `capture_native_player.py` and its
  account-wide capture lock. No manual UI or Chrome Computer Use was used.
  Every accepted capture includes `done`, verified embedded fighter paths,
  fresh LoadVars/run identity and locked source hashes.
- Source-only capture mode was used to decouple Flash recording from Godot
  execution. Its temporary `native.json` placeholders are **not** accepted as
  Godot evidence. Retained `*.native.json.gz` come from independent Godot runs.
- The unchanged comparator checks `frame`, `x`, `y`, `xscale`, `action`, `hp`,
  `ql`, `sw`, `touch`, `touchFloor`, `hits`, `paused`, `hstm`, `hurtSkling`,
  plus row alignment/completeness, with no tolerance or rounding changes.
- `prior_source_states_identical` compares canonical fighter rows against the
  earlier PR trace, independently of changed run IDs, RNG and clock log bytes.
  Both new raw hashes and old/new canonical state hashes are recorded.

## Gin-class adversarial coverage

The original 28 focused cases are replayed unchanged. New fixtures add mirrored
cancel and guard/break receive, super-preparation attack timing, and an immediate
opponent super after interruption. Target coverage is separate from equality.

### Super preparation and interruption

`source-review.json` records every frame script (including empty frames),
placement/MOVE/removal and receiver lifetime for the relevant source ranges.

- Orochimaru Sprite 541: normal super enters at 534, writes preparation state at
  535, retains the receiver through 538, removes it at 539, and calls `bsd` at
  540. The new input reaches super at tick 15 and hurt at tick 16; tick 17 HP is
  960. This is a real preparation interruption, unlike the old normal-interrupt
  fixture.
- Pain Sprite 573: super enters at 600, writes preparation state at 601,
  removes the receiver at 602 and calls `bsd` at 603. The same input timing
  reaches super at tick 15, hurt at 16 and HP 960 at 17.
- Jiraiya Sprite 342: all three super entries (608, 731, 818) have no `bdmn`
  receiver. In particular frame 608 removes depth 38 before the preparation
  state write at 609 and `bsd` at 611. Its attack-during-preparation case is a
  **protected/no-interrupt case**, not a successful interruption. Moving Ichigo
  closer in two Godot-only calibration attempts did not create a receiver;
  those attempts are diagnostics, not additional Flash acceptance samples.

For Orochimaru and Pain, `prep-counter-super` also holds P2 special at ticks
20–25. Ichigo's source Sprite 638 frame-181 callback permits `bisha()`, causing
frame 446 at tick 21 and super pause at 450/tick 25. The post-interrupt recovery
and pause must be assessed through the end of the trace, not just first damage.

The retained 544-byte `_clear_interrupted_super_preparation` block has SHA-256
`d39b2b50d96d37ac717e1d1e8e9ccd711a67f6bbadcee6afc30593d6e0caa91e`.
It is unchanged. Its direct-call smoke passing does not establish that all
source-controlled interruption paths recover; the new end-to-end cases are the
relevant evidence for that stronger claim. No broader anti-deadlock deviation
is introduced by this audit.

### Cancel windows and guard receive

- Mirrored Orochimaru keeps the original combo-to-super timing: source 260 at
  tick 50 to 534 at 51. Mirrored Jiraiya uses 187 at 16 to 608 at 17.
- Pain's frame-211 first-normal window does not accept ordinary `bisha()`.
  `cancel-super-mirror` is retained as an explicit **unsupported-cancel
  negative**, not counted as successful super coverage. Its new positive case
  uses down+attack and the actual frame-357 `bisha()` callback; input continues
  through hitstop and reaches 600 from 357 at ticks 36→37.
- Mirrored receive cases preserve the original two attacks: ordinary guard
  at ticks 10–13, then Ichigo down+attack at 80–83. The existing focused set
  independently covers chip, guard break, hitstun and super/ultimate receive.

### Warp, rush, scale, placement and masks

The fresh focused set includes Jiraiya's repeated target-relative warp and held
rush/contact branch, Pain's repeated mirrored warp and ultimate attraction,
and all three fighters' supers against guard. The state comparison checks
positions, facing and source frames at every tick, including pause and exits.
`geometry-source-check.json` additionally verifies that every source timeline
placement/change and the wrapper matrix agree with packaged JSON; it records
all mask frames. Per-case observations report which source mask frames were
actually visited. Orochimaru has 74 root frames with masks, Jiraiya 971, Pain 0.

This is a short state/transform sanity audit, not pixel parity. A correct actor
position or an identical mask definition does not prove the rendered mask,
child animation, sound, HUD, filters or full browser presentation. The fresh
`player_visual_smoke` is a shared renderer regression, not a three-character
Flash pixel comparison. Those areas
remain unaccepted; no screenshots or visual pass are fabricated.

## Live package identity

`live-package.json` records a read-only download from
`https://bvn26.vercel.app/`, its metadata and actual PCK hash. The PCK was loaded
into an otherwise empty temporary Godot project, preventing missing resources
from falling back to the checkout. All 42 JSON resources for these three
fighters are byte-identical to current master. Embedded and sidecar commit
identities are `2d3336bf039e7ad0ac92c22423273f664b432225` and the downloaded PCK
matches the published SHA-256.

The packaged online manifest has the same roster but different compatibility
fingerprints from the checked-in manifest. This is disclosed separately:
`build_web.sh` binds export presets and regenerates fingerprints after import.
After the ordinary Godot import, the content fingerprint also exactly matches
the live package. The one added content input is the generated Orochimaru
`player_controller/body.gd.uid`; its hash is recorded in `live-package.json`.
The build fingerprint is not independently reproduced (the staged template
path participates in it). No claim is made that the checked-in fingerprint
itself is shipped unchanged.
No Worker or Vercel deployment, room creation or merge was performed.

## Reproduction

Use the retained existing fixtures under each character and the new `cases/`
subdirectories here. Build one fresh dynamic probe per fighter with
`build_ai_reference.py --dynamic-move-case --frames 240`, the selected source
character, `--p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂` and an explicit
fixture. Run `test_move_references.py --capture-only` against each case folder,
with the persistent player and `--allow-window-activation`.

Execute those same fixtures with `res://tests/move_case_reference.gd` using
`--batch`, then compare the real Godot JSON with collected `events.jsonl` via
`tools/probes/compare_mode_reference.py`. Allow a sufficient wall-clock timeout
for the batch. The first eight-case native attempt exceeded the helper script's
140-second budget; it was excluded and rerun with a 900-second batch timeout.
This changes harness time only, not fight ticks, traces, inputs or thresholds.
Temporary SWFs, engine caches, downloaded PCK and raw workspaces stay in `/tmp`.
Only compact audit evidence is retained here.
