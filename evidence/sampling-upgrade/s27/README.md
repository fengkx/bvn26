# s27 — Case-bound native capture adapter

Execution base: `8f80ae0e` (master); branch `feat/sampling-native-adapter`.
This slice connects required-native sampling to the existing static move-case
probe and `capture_native_player.capture`. No runtime/importer changes.

## Shipped

- `python3 -m tools.sampling_native` launches the existing Flash capture API and
  seals a receipt only after validating case identity and capture completeness.
- `sampling_matrix run/check --native-evidence DIR` requires `<case-id>.json`
  receipts for required cases. Run binds receipt hashes into its report; check
  revalidates artifacts and rejects changed receipt bindings.
- Full tape equality, selected fighters/helpers/stage, non-AI mode and capture
  duration are checked against build metadata. Logs must have contiguous event
  sequence numbers, exactly both actors at ticks 0–60 in order, complete state
  payloads, finite geometry/resources, the requested tick-10 posture, and one
  terminal done event. Timeout/foreign-run/truncated/duplicate events fail.
- Source SWFs, build metadata and declared outputs, instrumentation diff, probe
  sources, parser/adapter, reference-environment document, player executable,
  tape and raw capture bytes are hash-bound and re-read on validation.

## Validation and limits

`focused-tests.txt`: **45 tests passed**. The positive test uses a clearly
synthetic static-build/log/player fixture for one Didala ground cell and mocks
Godot execution. It exercises required-native `run`, receipt binding, false
parity/admission flags, and rejection of full-campaign check with only one
receipt. It is **not a native Flash capture** or an added fighter execution proof.
The capture-command test mocks the native player boundary and confirms reuse of
the existing capture API; failed capture produces no new receipt. Integrity,
handoff and schema checks pass (schema checks use the pinned requirements-dev
dependency in an isolated temporary venv).
Negative tests cover missing receipts, wrong case/configuration/duration,
dynamic fixtures, missing/duplicate/foreign/incomplete events, wrong posture,
nonfinite state, missing SWF bindings, mutated artifacts and false parity claims.

Receipts are local audit records, not authentication against a malicious author.
The build must come from the reviewed builder; matching metadata cannot prove
arbitrary SWF code implements that tape. Absolute artifact paths must remain
available; moving/deleting them fails validation. Dynamic fixture loading and
asynchronous post-done tails are deliberately rejected in this first adapter.
No pixels, hitboxes, child display list, full camera or DoAction coverage is
claimed. Random/timer events are retained in the raw capture but no same-random
replay or behavioral comparison is implemented. Jinye/Yijiao residuals remain
known gaps. `native_parity_proven=false`; `production_admitted=false`.

## Reproduce the fixture gate

```sh
python3 -m unittest -v tools.tests.test_sampling_native tools.tests.test_sampling_matrix \
  tools.tests.test_move_cases_paths tools.tests.test_move_cases_targets \
  tools.tests.test_move_acceptance_harness
```

## Native use (not executed in s27)

Use the Player Debugger 32 environment described in
[reference-environment.md](../../reference-environment.md). Paths below are
examples; keep the build and capture artifacts for later validation.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/s27-campaign --fighters didala --require-native
python3 tools/probes/build_ai_reference.py --ffdec /path/to/ffdec.jar \
  --output /tmp/s27-build --run-id s27-unique --frames 60 \
  --move-case /tmp/s27-campaign/cases/didala__attack__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂
python3 -m tools.sampling_native \
  --case /tmp/s27-campaign/cases/didala__attack__neutral__ground__near.json \
  --build /tmp/s27-build --trace /tmp/s27-capture.log \
  --receipt /tmp/s27-receipts/didala__attack__neutral__ground__near.json \
  --allow-window-activation
python3 -m tools.sampling_matrix run --campaign /tmp/s27-campaign \
  --output /tmp/s27-runtime --godot /path/to/godot \
  --cases didala__attack__neutral__ground__near --native-evidence /tmp/s27-receipts
```

This selected run remains 1/324, never full coverage. `check` requires all 324
receipts and runtime traces. Next thin step: run this one real native cell and
retain its artifacts; no full-roster native run is required to review s27.
