# Sage Naruto / 仙鸣 independent author lane

Base: `a3b479414546250b7d0cd6e35cbc3ae52b3169d1`.
Branch: `port/minrenx-base`. Source-first base and required transformation are
integrated in this branch. The release Web export and packed-form check pass; foreground Web gameplay
validation is blocked by the confirmed locked Mac desktop. Full parity and
production admission remain false. No Draft PR has been opened yet.

## Roster identity

`roster-audit.json` records every fighter selector card in source display-list
order, joined to the pinned available registry, catalog and coverage rows.
The first remaining standalone card is 仙鸣 (depth 73, `minrenx.swf`), followed
by 一护2 (depth 77, `ichigo.swf`). The latter belongs to another author lane.
石田 is already `yulong` in both the available registry and matchmaking catalog.
Temari is reserved to `port/shouju-base` and was not changed.

The source catalog in `scripts/main.json:frame_6/DoAction.as` defines 仙鸣
separately from `minren.swf`; 黄金鸣人 is its `WKframe=2` clone. Internal
bankai, nine-tail and curse forms already present in generated form packages
are excluded from roster selection, regardless of coverage status.

## Source-first record

1. `source-first.json` indexes all 2,999 body frames, including script-free
   frames, display changes and events. Full extracted timelines retain source
   matrices, placements and nested definitions. Base Sprite 449 has 1,308
   frames; replacement Sprite 1172 has 1,691.
2. Root parent frame 1 places Sprite 449 at depth 1; parent frame 2 replaces
   it with Sprite 1172 at the same depth. Their load declarations independently
   initialize instance fields; base speed is 10, replacement speed is 14.
   Native anonymous handles are materialization-only, not source instance names.
3. The transform enters 万解 at 1278. Frame 1279 subtracts 300 energy;
   frame 1281 calls `wankai_start`, whose source subtracts another 300.
   Both authored calls are retained. Frame 1294 calls `wankai`, transfers HP
   and energy, registers `feixue` when not invulnerable, then advances the
   parent frame. Frame 1297 also contains an explicit parent goto to frame 2;
   it is compiled without assuming it is reached after replacement.
   No label end is treated as an invented return to standing.
4. The form graph dry-run recompiles both nodes and applies existing placement,
   visual-control, blend and form-package guards. The source-derived frame-call
   fragment is separately validated. The unchanged global guard continues to
   reject the unregistered new character. No calls or guards were removed.
5. Fresh original-player evidence uses the approved foreground reservation and
   `/Users/fengkx/me/agent-code/.locks/flash_lock.py`, holder
   `bvn-lane2-next-port`. Captures use new LaunchServices instances and never
   operate PID 24366. `build_timer_probe.py` observes authored callback entry
   and exit; timer delivery must be taken from these observations, not guessed.

| State | Owner | Write / preservation / cleanup | Source |
|---|---|---|---|
| Movement and input locals | Body instance | New parent placement initializes; replacement gets its own declarations | Root frame 1/2 load callbacks |
| Transfer HP and energy | Fighter wrapper | `wankai` saves; replacement `doWanKai` restores | Body frame 1 functions |
| `feiint` handle | Root interval registry | Source clears old handle before registration; callback retains its original body closure | `wankai` / `feixue` |
| Callback damage | Retained callback plus live body | Unpaused and captured HP above one fifth max; invokes authored `loseHp(10)` | `feixue` |
| Hit/contact flags | Source placement / receiver | Existing source compiler and registry lifecycle; no per-character resets | Extracted body and nested timelines |

## Rebuild

Use Python >= 3.10 (this host's `/opt/homebrew/bin/python3`), pinned JPEXS
26.2.1 and Godot 4.7.2. Export locked `game/fighter/minrenx.swf` with
`tools/importer/export_swf_xml.py` to a fresh scratch directory, then run:

```sh
python3 evidence/characters/minrenx/build_port.py \
  --workspace /tmp/bvn-lane2-minrenx-export \
  --ffdec /Users/fengkx/me/agent-code/toolchains/jpexs-26.2.1/ffdec-cli.jar \
  --ffmpeg /opt/homebrew/bin/ffmpeg
```

This rebuilds only the two character packages and their source intermediates.
Form activation for local diagnostic fixtures is in the character's own
`form_profiles.json`; it does not admit the character to the shared roster.
The shared frame-call requirement is retained as a fragment for serial integration.

## Integration and residuals

At `82b5ad6d4`, shared roster wiring was withheld under an overly broad reading
of the parallel-lane restriction. The user clarified that required in-repo wiring
belongs in this same branch. Selection, catalog, portraits/footer, natural opening,
reviewed frame-call obligations and the actual shared menu font are now integrated.
No other worktree or parallel character package was copied or changed.

The actual `tools/importer/build_menu_font.py` now covers dynamic available-roster
labels and was run against this branch. `font-integrated-check.json` verifies all
502 required glyphs, including 仙鸣. The earlier isolated candidate and 455-glyph
baseline receipts remain historical evidence. Catalog ordering was made consistent
with available (including the pre-existing Kenshin order mismatch); guards were
not relaxed. The source selector's card order remains unchanged.

All six proof/admission flags remain false. Early incomplete-import diagnostics
and later headed exit RID/ObjectDB/resources-still-in-use errors remain unaccepted.
`native-visual-execution.json` separates completed image capture from exit cleanup.

## Fresh targeted behavior evidence

The accepted targeted set contains 22 fixtures and 16,364 paired character-state
rows, with zero differences across the comparator's 14 fields. See
`comparisons.json` (13 base cases), `form-comparisons.json` (7 transformation/form
cases), `cancel-comparisons.json` (one source-window cancel), and
`crossing-comparisons.json` (one uninterrupted three-cast jumping crossover).
The base set includes one insufficient-energy negative; it must remain separate
from successful move reachability. The five post-transform move fixtures explicitly
refill energy at tick 100; these are controlled interventions, not full matches.

The jumping crossover casts face right, left, then right (ticks 11, 211, 411),
without recreating the fighter. The older walking-only fixture also matches
1,202 rows but never crosses the opponent; `walking-comparisons.json` is diagnostic
and excluded from the 22-case total. No original inputs or tolerances were changed
to turn that diagnostic into crossing evidence.

`godot/tests/minrenx_form_lifecycle.gd` separately checks a controlled transform
edge, transferred state, fresh local initialization, pause/resume, HP threshold,
checkpoint replay and next-round form retention. Its clean receipt is
`logs/form-lifecycle-r03.log`. It is not an original-player input replay.
`checkpoint-frame-calibration.json` preserves the initial wrong test expectation
and the fresh Flash observation used to correct it; runtime behavior was unchanged.

`runtime-hashes-during.json` records 807 runtime/package hashes during capture;
the final receipt verifies they stayed unchanged. This is explicitly not a
before-capture hash snapshot. Capture build metadata, instrumentation diffs,
events, clock/random tapes and fixtures are retained. Temporary `game` symlinks
are inventoried in `excluded-scratch-links.json`; rebuild those scratch games from
the recorded source instead of depending on absolute temporary paths. Capture
folders' legacy `native.json` files are collector output, not Godot evidence;
Godot outputs are in the explicitly named `native-*` directories.

## Resumed targeted delivery

The former integration blocker is resolved in this worktree. `integration-plan.json`
and `shared-integration-blocker.json` retain its history and the user's clarification.
The initial 22-case set below remains immutable; `receive-comparisons.json` adds
normal guard, incoming guard/guard break and interruption: 25 cases / 18,530 rows
in total. Normal guard chips the opponent by 3 HP with zero hits; incoming
guard then low attack leaves Sage Naruto at 916 HP / one hit; interruption
leaves 960 HP / one hit (`receive-observations.json`). Failed wall-clock-limited attempts are retained in r01/r02 logs; the final
native r03 and original r02 captures complete all 360 logical frames unchanged.

`minrenx_rollback_smoke.gd` passes natural opening, ultimate pause checkpoint/replay,
late guard inputs through the production rollback session and next-round reset.
Native selection, super and required transformed-form images were inspected in
`screenshots/` and `form-screenshots/`. They demonstrate rendering, not pixel parity.
The headed exit leaks remain explicitly unaccepted and are not hidden by marker checks.

The initial saved-roster/targeted receipt is `pre-integration-validation.json`.
The old `finalize_evidence.py` seals that pre-integration phase and intentionally
expects its historical baseline; it is not the resumed integration finalizer.
The official local release Web build passes strict import/export error scans,
manifest checks and online UI checks. Its PCK SHA-256 is
`7121947e451eef8cbf0003ac88ad00ee956a81f9871e8ff0b958838e420313af`.
`web/source-freeze-check.json` matches 17,008 runtime files plus catalog/guards
to this branch; the build truthfully records working-tree changes atop `82b5ad6d4`.
The exported required form passes `packed_profile_check.gd`, including rejection
of a missing form. This does not substitute for foreground browser gameplay.

Two headed CDP attempts remain failed: r01 never entered a match; r02 explicitly
stopped before input because the canvas was focused but the page was hidden.
Read-only system inspection at 15:26 Asia/Shanghai confirmed both
`IOConsoleLocked` and `CGSSessionScreenIsLocked`. No unlock was attempted and
foreground retries stopped. `web/execution.json` records the exact blocker;
`web-r01/` and `web-r02/` retain failures. The user renewed the exclusive reservation at 17:28 Asia/Shanghai. A single
locked preflight at 17:31:44 acquired the specified lock, confirmed the desktop
was still locked, and stopped before launching a browser. The lock was released;
no unlock or input was attempted. See `web/foreground-preflight-r03.json`.
The two earlier browser failures remain unchanged. After the user unlocks the
desktop and indicates readiness under the valid reservation, rerun
`web_smoke.mjs` under the specified exclusive lock against the same built artifact.
This historical blocker was resolved by the user unlocking the desktop at 19:34.

`seal_integration.py` updates required repository hashes and truthfully seals
either the passed state or this explicit browser blocker. It cannot convert a
blocked run into a Web pass. All six proof/admission flags remain false.

## Final saved-roster regression

The pinned-base saved roster passed 300 cases / 189,400 state rows: the inherited
288-case runner plus the 12 Weqal cases introduced at the pinned base. This does
not include parallel author lanes. `saved-roster-report.json` and
`saved-weqal-report.json` contain execution and comparison results; their matching
archives retain every new native state output and process/engine log. Original
saved Flash traces remain in the pinned repository and were hash-checked before
replay. Exit residuals are listed separately in `validation-summary.json` and
are not accepted by the state-match result.

`validation-summary.json` is the final scoped receipt. `artifact-manifest.json`
hashes the durable lane files and packages; it is not a global release manifest.

Raw instrumentation diffs retain source CRLF/trailing whitespace and raw logs retain
their original ending. Whole-evidence `git diff --check` reports those bytes;
the authored code/metadata check passes (`diff-check.json`). Captured evidence
was not normalized to silence a whitespace check.

## Unlocked headed Web validation

At 19:35–19:37 Asia/Shanghai, r04 and r05 ran under the exclusive
`bvn-lane2-next-port` lock against the retained local release PCK. Both CDP
keyboard sequences passed normal selection, natural opening, movement, combo,
super and J+K replacement into `minrenx-2`, recovering to standing. Build
identity matched; no JavaScript exceptions or Flash/Ruffle requests were recorded.
The isolated browser closed before the lock was released. Flash PID 24366 was
never operated.

CDP screenshots show a black canvas and cannot prove rendering. The r05 macOS
system screenshots show the selection portrait/footer, red-cloak base fight and
golden replacement. Published screenshots crop only the browser window to avoid
unrelated desktop UI; original hashes and crop coordinates are in
`web/visual-review.json`. This is targeted display review, not aligned Flash
pixel/audio parity or physical OS keyboard testing. r01/r02 failures, r03 locked
preflight, and r04 black CDP captures remain preserved. Native headed exit
resource/RID leaks remain unaccepted and are not treated as full-port admission.
