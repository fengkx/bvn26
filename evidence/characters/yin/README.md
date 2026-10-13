# Gin / 银 (yin), 2026-10-13

Imported from `22fed0a7` using the existing Renji-compatible pipeline. No compiler
rules or production runtime code changed. One form, Sprite 435, 1,212 frames;
all movement, five normal attacks, directional/air moves, three supers, summon,
guard/hurt/recovery, opening and result labels are retained. The original card,
five portrait frames, footer name, local/online roster and fingerprints are wired.
The existing four assists remain selectable; default Kenpachi (`jianba`) is deferred.

## SOURCE_FIRST five questions

1. All 136 Sprite 435 scripts are indexed in `data/slices/yin-base.json` and
   retained at their original paths in `scripts/fighter/yin.json`. Every frame,
   including empty frames, is in `data/slices/yin-base.timeline.json`. Controller
   Sprite 16, receiver Sprite 2 and Sprite 435's frame-1 body are byte-identical
   to Renji's corresponding scripts (checked in `test_yin_import.py`).
2. The timeline preserves new placements, MOVE, removal and depth. Examples:
   motion at `frame_199/PlaceObject2_16_33`, replaced by the combo controller at
   frame 202; retreat at `frame_421/PlaceObject2_16_36`; guard receiver at
   `frame_964/PlaceObject2_2_31`; hurt motion at frame 989. Generated controller
   hooks retain placement and member frames; new callbacks begin the following
   tick. Hitboxes use the original matrices, bounds and instance lifetimes.
3. Exits come from source, not label boundaries: normals return at
   217/245/273/304/335; supers at 641/742/895; guard recoil at 984; hurt at 997;
   knockdown at 1042; recovery at 1058; opening at 1119. Frame 993 stops hurt
   playback until `beidax` releases it. Super pause starts/ends at
   579/602, 652/674 and 768/800. Conditional cancels retain source predicate
   order and clip lifetime (202, 232, 258, 291, 379, 458, 553, 964, 980).
4. Checks lock source invariants: exact placement/cancel windows, rounded
   forward/retreat motion, original `gjl1` packets, 976 `onDefence`, 988
   `onBeHit`, 1001 `onBeHit(true)`, and super events. Sprite 2 implements chip
   damage `/10`, `zl > 10` guard break, `hdtime * 30/1000`, and source reaction
   labels. No hitboxes, damage, recovery lengths or thresholds were guessed.
5. Focused fixed-input fixtures in `cases/` run both the instrumented original
   and production Godot battle. Results and trace hashes are in `checks.json`.
   These cover combo/cancel execution, ordinary interrupts, guard/chip,
   multihit supers, guard break, and Gin's own guard/hurt chain. They are not
   a broad boundary matrix or full audiovisual parity claim.

## Validation and limits

See `checks.json` for exact results. The light `yin_rollback_smoke.gd` starts a
real selected Gin match, completes the natural intro, restores a checkpoint
during ultimate super pause, replays through guard/guard-break settlement,
compares the full simulation state, and checks the source next-round reset.
Existing Python, core Godot, online-manifest, matchmaking and handoff checks
are also recorded there, including identical master failures.

**Accepted Flash deviation:** the user explicitly chose to keep
`FighterRuntime._clear_interrupted_super_preparation`. A real hit before `bsd`
clears the orphaned `bs` lock to prevent the original deadlock. This shared fix
is unchanged; ordinary interrupt/cancel and guard rules retain source behavior.
Full visual/audio, browser and AI parity are not claimed. Voice linkage names
are absent in the locked source, as with existing fighters; none are invented.

## Reproduce

Use Python >=3.10, Godot 4.7.2, JPEXS 26.2.1 and the unchanged locked inputs.
Run `extract_fighter_slice.py 银`, then the geometry/combat/materialization
commands from `docs/OPERATIONS.md` with `yin`, Sprite 435 and `yin-base`.
Compile `compile_ai_controller.py` and `compile_ai_body.py` into both
`player_controller` (`--player`) and `ai_controller`; retain the existing
`player_body` artifact convention. Compile context, hit state and hurt voice,
bake sound segments, and compile the source opening. Portraits/footer use
`build_selection_portraits.py ... 银` with temporary output, merged under
`portrait-yin-*` / `footer-name-yin.png`. Rebuild `build_online_manifest.py`.

The reference player is persistently installed at
`/Users/fengkx/me/code/flash-player/Flash Player.app`; pass it explicitly with
`--player-app`, never depend on a mounted volume. Adobe 32.0.0.465 DMG SHA-256:
`7a9a043e1481768d58ed9de8ff8644aa95d73ea7a0f5ba59b77fd4e71f7c25fd`;
executable: `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
Downloaded from the official URL recorded in `evidence/reference-environment.md`.
Build a dynamic fixture probe with `build_ai_reference.py --p1-character 银
--p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --frames 240
--dynamic-move-case --move-case .../cases/combo.json` and run
`test_move_cases.py` / `test_move_references.py` with these same fixtures.
Raw captures stay in `/tmp/yin-original-focused-r1` and
`/tmp/yin-original-receive-guard`; they are not production dependencies.
