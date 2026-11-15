# Sage Naruto / 仙鸣 independent author lane

Base: `a3b479414546250b7d0cd6e35cbc3ae52b3169d1`.
Branch: `port/minrenx-base`. This is an in-progress source-first candidate,
not full parity or production admission. No PR is justified by compilation alone.

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
455 declared characters. Its regenerated artifact and provenance are kept in
`font/`; the shared menu font was restored byte-for-byte to the pinned base.
No shared catalog, available registry or global manifest is overwritten.

All six proof/admission flags remain false. Full audiovisual parity, exhaustive
AI and boundaries, production admission, and headed exit-leak acceptance are
not established. The initial native diagnostic ran before first asset import
finished and contains missing-resource errors and exit leaks; it is retained
but cannot count as a clean native pass. Fresh source/native comparisons and
final check receipts must be consulted separately from build success.
