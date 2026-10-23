# Original reference environment

Status: usable for native-player boot and isolated AVM1 scheduling probes. A fixed
Naruto-versus-Ichigo gameplay replay has not yet been captured, so `M0-02` remains
pending.

## Runtime

- Player: Adobe Flash Player Debugger `32.0.0.465`, standalone macOS application
- Bundle identifier: `com.macromedia.Flash Player Debugger.app`
- Team identifier: `JQ525L2MZD`
- Executable architecture: `x86_64`, run through Rosetta on Apple Silicon
- Executable SHA-256: `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
- Installer URL: `https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa_debug.dmg`
- Installer SHA-256: `7a9a043e1481768d58ed9de8ff8644aa95d73ea7a0f5ba59b77fd4e71f7c25fd`
- JPEXS: `26.2.1`; CLI jar SHA-256:
  `23c1e70ff2b08388e35de10afd97a2875386cbfdc2ef99c8176d40b4f8a3ada9`

The locked `game/main.swf` was opened directly from its original directory on
2026-09-07. It reached the BVN 2.6 main menu and displayed the Normal single-player
selection and keyboard-help overlay. No file under `game/` or `scripts/` was
modified. This establishes a working native reference player, but not yet a
repeatable gameplay oracle.

`trace()` capture uses the two settings in `tools/probes/mm.cfg`. Probe SWFs are
built in a temporary/output directory and are not production dependencies.

## Known limitations

- The debugger is an end-of-life reference runtime and must never ship with the Web build.
- The initial full-game navigation was visually observed; its input stream and frame trace
  have not yet been normalized into an oracle replay.
- Ruffle is not used for scheduling conclusions because the full game did not provide a
  stable reference run there.

## Filter probes, 2026-10-23

The packaged filter probes were rebuilt with JPEXS 26.2.1 and recaptured with
Adobe Flash Player Debugger 32.0.0.465 through Rosetta. The executable and JPEXS
hashes match the locked values above. Probe programs, reproducible commands,
raw traces and per-run metadata are recorded in
[filter probe instructions](../tools/probes/flash_filters/README.md) and
[filter r02 evidence](importer-loud-fail/r02/README.md).
Godot 4.7.2 Compatibility ran on Apple M2/OpenGL Metal; a fresh signed official
app was used because the older scratch app failed signature verification.
No source file under game/ or scripts/ was changed.

## Filter color and shipped components, r03 (2026-10-23)

The same locked Flash Debugger/JPEXS executables and Godot 4.7.2 Compatibility
environment captured the color/opacity/order diagnostics and 21 shipped filter
or cache placements. Raw captures, source hashes and per-run metadata are in
[the r03 evidence](importer-loud-fail/r03/README.md). Native capture used
tools/probes/capture_native_player.py (component harness delegates to it).
Direct black-background RGB avoids lossy getPixel32 premultiplication recovery.
45/54 real component images still differ; these captures do not certify parity.

## XG_rush asset probe, r05 (2026-10-23)

The same Flash Player Debugger 32.0.0.465/Rosetta and JPEXS 26.2.1 captured the
original XG_rush definition tags through capture_native_player.py. No original
definition bytes changed during probe import. Native logs, actual probe scripts,
player executable hash and capture metadata are in
[r05 evidence](importer-loud-fail/r05/README.md). Godot 4.7.2 Compatibility
matches 21 entered source frames, but sampled RGB still differs. The timer-based
phase experiment is explicitly not used as the native frame oracle.

## Rukia numeric goto, r06 (2026-10-23)

The locked Flash Player Debugger 32.0.0.465/Rosetta and JPEXS 26.2.1 captured
an isolated Rukia body with its original definition tags and frame actions.
Godot 4.7.2 matches all 31 sampled playheads across the original 141→130 loop.
This is a paused-movement playhead experiment, not whole-combat equivalence.
Build hashes, source, raw trace and capture environment are in
[r06 evidence](importer-loud-fail/r06/README.md).

## Parent form replacement, r07 (2026-10-23)

Four original fighter SWFs were captured with the same Flash Debugger 32/Rosetta
and JPEXS 26.2.1 through capture_native_player.py. The root probe initializes the
required pause flag before original startup and then forces the original body
frame containing the parent goto. All non-DoAction root tags and original nested
definitions are byte-identical. The captures record native behavior only; there
is no matching Godot form-switch consumer yet. See
[r07 evidence](importer-loud-fail/r07/README.md) for raw traces and environment hashes.
