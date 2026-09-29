# LAG-01 local build identity evidence

Date: 2026-09-29

## Scope

This package changes only the Web build pipeline, build metadata tooling, and
focused build tests. It does not modify combat state, input handling, timeline
scheduling, timers, random-number order, or online messages. The staged export
uses one copied Godot project snapshot for manifest generation, metadata, import,
tests, and export. The staged Web release preset is bound to the exact template
file whose SHA-256 is recorded. The Vercel path falls back to
`VERCEL_GIT_COMMIT_SHA` only when `.git` is absent and fails closed without a
commit identity.

## Local verification

- `python3 tools/tests/test_web_diagnostics_metadata.py`: 6 tests passed,
  including staged-tree dirty paths, Vercel-without-`.git` fallback, missing
  commit failure, and removal of a stale sidecar after finalization failure.
- `python3 tools/tests/test_build_web_pipeline.py`: 4 tests passed. They verify
  template hash-to-preset binding (including a path with spaces), stale-sidecar
  cleanup on preflight failure, and rejection of `SCRIPT ERROR` / `Parse Error`
  even when a fake Godot process exits 0; the raw mocked log is retained. The
  log scanner reports only the exact macOS CA `ret != noErr` message adjacent to
  `get_system_ca_certificates` as an environment warning; other `ERROR:` lines
  and the same message without its immediately adjacent location remain fatal.
- `bash -n tools/build_web.sh`, Python compilation, and `git diff --check` passed.
- `python3 tools/verify.py`, `tools/check_handoff.py`,
  `tools/validate_contracts.py`, and `tools/build_online_manifest.py --check`
  passed. The online manifest was regenerated with build fingerprint
  `098c35680513f77b333348fce5a397af38b95e4421e865b6d774d22526ddfb16` and
  content fingerprint
  `a52c9b9391f280f06bb5b205607fccdf23f9fe3afade41fbaecc003d5bb063e7`.
  `manifest.json` changed only the `fighter_runtime.gd` and
  `helper_runtime.gd` hashes; locked `game/` and `scripts/` hashes were not
  changed.

## Final Godot/Web export and local browser identity

Environment: macOS 24.6 arm64, Godot 4.7.2 at
`/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot`. The
coordinated build began with reported system load around 44; no performance
comparison was made. The staged source snapshot was frozen at
`2026-09-29T06:19:22Z`. Import and export both exited 0; the raw logs are
retained outside the repository at:

- `/private/var/folders/t7/n5qfrxps1hq4pmj58wsspmww0000gn/T/bvn26-web-build-logs/20260929T061907Z-58572/import.log`
- `/private/var/folders/t7/n5qfrxps1hq4pmj58wsspmww0000gn/T/bvn26-web-build-logs/20260929T061907Z-58572/export.log`

Both scans reported `markers=none`: no `SCRIPT ERROR`, `Parse Error`, or
unrecognized Godot `ERROR:` marker was found. The logs contain only the exact
macOS certificate `noErr` warning and the editor-settings save warning that the
scanner identifies as environment warnings. Staged online-manifest generation
and its tests passed. The source manifest check reports build fingerprint
`098c35680513f77b333348fce5a397af38b95e4421e865b6d774d22526ddfb16`; the
exported stage manifest reports
`763831e847af98f27a3ab3c1feed1c6e0cfa66921464e126735df13d3bf923ed` with the
same content fingerprint
`a52c9b9391f280f06bb5b205607fccdf23f9fe3afade41fbaecc003d5bb063e7`. This
build-fingerprint difference comes from binding the staged `export_presets.cfg`
to the actual local template path before generating the manifest. The absolute
template path remains stage-only; it is not written into the source preset or
source manifest. The artifact conservatively identifies this template-bound
build rather than treating a different build artifact as compatible.

Final sidecar: `dist/web/build-metadata.json`. Its build ID is
`f27cb94d3646c65406c4b3cc4b39b07c4346a91c6aeaaead98512454151fb290`, Git
commit `fb9a134688d4fa8f56380287df30df856463e295`, `dirty=true` with 24 staged
paths, and source-tree SHA-256
`33280967ea5e0d7ea1cae419f88fdc3c388f094b91f49768fc8312616eb11dd1`. Godot
4.7.2 used the release template with SHA-256
`d3ee2f08cef0cf3cf6678a6355a92a8db48ccdd35cbd2e8bfd5f0e8a0b4032a0`. The
sidecar PCK SHA-256
`39acc71781cac1a3349a53dace40a571ee86d4fedb105a477ce3f4336e44b6b7` matches
the actual `dist/web/index.pck` (109,175,960 bytes). The copied root export set
contains `index.html`, JS, WASM, PCK, both audio worklets, and all three PNG
icons; the unrelated `dist/web/_webrtc_transport` directory remains present.

The root agent served this exact local artifact at `127.0.0.1:8042`, opened it
in IAB, and exported a browser diagnostics log. The downloaded file remains at
`/Users/fengkx/Downloads/bvn26-log-2026-09-29T06-22-34-133Z.json` (SHA-256
`c9739b863820a2a45ad1f427f5ce3788cca37e67d320cb2b3a7a8a1da1278e83`). Its
`build.status` is `match`; its `buildID` and `sidecarBuildID` both match the
final artifact ID above, and its PCK hash matches the sidecar. The original
download was not moved or modified.

No deployment or two-machine field run was performed. A diagnostics log from
the actual deployed page and the M0 field gate remain pending; the local IAB
identity check does not satisfy those release gates.
