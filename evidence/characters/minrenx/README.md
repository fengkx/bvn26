# Sage Naruto / 仙鸣 independent author lane

Base: `a3b479414546250b7d0cd6e35cbc3ae52b3169d1`.
Branch: `port/minrenx-base`. This is a source-first candidate awaiting serial
integration, not full parity or production admission. No Draft PR has been opened.

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

## Shared-file boundary and residuals

The real `build_menu_font.py` regeneration and output cmap check passed for
455 baseline characters. A follow-up staged candidate applies `font-builder.patch`
to include dynamic available-roster labels and passes 502 characters, including
仙鸣. Its regenerated artifact and provenance are kept in
`font/`; the shared menu font was restored byte-for-byte to the pinned base.
No shared catalog, available registry or global manifest is overwritten.

All six proof/admission flags remain false. Full audiovisual parity, exhaustive
AI and boundaries, production admission, and headed exit-leak acceptance are
not established. The initial native diagnostic ran before first asset import
finished and contains missing-resource errors and exit leaks; it is retained
but cannot count as a clean native pass. Fresh source/native comparisons and
final check receipts must be consulted separately from build success.

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

## Delivery blocker

The standard selectable roster does not yet register this candidate. Shared
available/catalog entries, selection portrait/footer and intro indexes,
reviewed frame-call requirements and global manifests must be integrated serially
with the other author lanes. `integration-plan.json` describes these edits;
`selection/`, the reviewed frame-call fragment and the staged font are durable
inputs. The unchanged global frame-call guard correctly rejects the unregistered
character; it has not been bypassed for release.

Consequently this lane does not meet the Draft PR delivery bar. Actual Web
selection/gameplay, aligned visual/effect-instance and audio evidence, and clean
headed exit behavior remain unverified. Early missing-resource/RID/ObjectDB
failures are retained and not accepted. The base headless batch also records
sandbox user-log write errors despite matching all states; later explicit-log
form/lifecycle runs are clean. No claim of complete 1:1 behavior is made.

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
