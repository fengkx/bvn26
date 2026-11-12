# G0 instrumentation dry run — NOT A PASS

2026-11-12: development-machine headless Chromium, Godot 4.7.2 release Web export.
See [handoff](../../../docs/G0_INSTRUMENTATION.md) and [summary](dry-run.json).
This proves instrumentation and a fixed single-player workload execute, not weak
hardware suitability, production parity or a host-authority MVP.

Verified:

- Eight Python tests: wrapper signature drift/early return structure, deterministic
  complete tape, source targets, interval union, paired quantiles, missing timing,
  and complete report/invalid submit correlation.
- Godot `timing_smoke.gd`: nested exclusive accounting, materialization outside
  advancement, reset and disabled collection; `G0_TIMING_SMOKE_OK`.
- Final Web run: all 900 ticks, actual super activity, nonzero advancement and
  materialization, raw render counters, browser intervals, input-to-submit joins,
  no browser exceptions/console errors; analyzer accepted the final report.
- `tools/verify.py`, `tools/check_handoff.py`, `tools/validate_contracts.py`,
  JavaScript syntax checks and `git diff --check` passed.
- Production `godot/`, locked `game/` and `scripts/` have no changes. Manifest
  changes only refresh the reviewed STATUS/task-document hashes.

The raw report, engine logs, downloaded tools and staged project remain outside
source under the OS temporary directory, not `/tmp`. The summary records the raw
report hash and export hashes; its source identity intentionally says dirty because
this was a pre-commit validation. The submitted source produces a newly identified
pack; reuse the exact same exported pack for comparisons.

Import/export emitted the existing sandbox editor-settings-save diagnostics;
there were no GDScript parse/compile errors. Earlier dry runs were rejected for
missing release-side initialization or stale cache UIDs. Neither is acceptance
evidence. The final browser run used rebuilt resource UID/export caches.

Not run: target weak machine, headed interactive/physical input latency,
Firefox/Safari, native Flash/FDB/debugger/live captures, network/multiplayer,
production deployment, GPU completion or time-to-photons. Renderer-counter frame
alignment and complete guest CPU accounting remain unqualified. G0 and all
existing admission/proof flags remain unchanged/unpassed. Actual person-days
were not tracked and remain null in the task table.
