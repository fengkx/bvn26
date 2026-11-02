# s277 — Actual loader read-to-target qualification (unproved)

Base: master `bab9d85693b5a4343dc20f7f8a7ce7f88e4e20a8` / #154.
Branch: `feat/s277-loader-attestation`.
Exclusive authority: [AFTER-s272 rank 5](../next-fix-priority-after-s272.md).
`production_admitted=false`; `native_parity_proven=false`;
`loader_attestation_proved=false`; M0-02 pending; zero product obligations closed.

**No independent consumed-byte/request/callback observation was qualified.**
The real wrong-resource load and bounded target lifetime remain unobserved.
This is an evidence-only diagnosis of the first prerequisite, not a successful
loader implementation. No historical receipt or `runtime_fighter` is repaired.

## Bounded extension beyond s268

[diagnose.py](diagnose.py) reuses the unchanged s268 archive/complete-stream
checker for **s259 normal P1 only**. It verifies the 5,503-event stream against
its receipt hash, sequence/structure, archived outputs and locked sources.
Those hash comparisons establish provenance, never live consumption.
[diagnosis.json](diagnosis.json) retains the full result and keeps all missing
live observations `null`. Held and Chad captures are not extended or rerun.

The new source audit compares original and archived
`scripts/main.json#DefineSprite_1900/frame_1/DoAction.as`:

- One `MovieClipLoader` serves `loadman("p1")`, `loadman("p2")`,
  `loadfz("p1")`, `loadfz("p2")`, then the separate `loadSound()` step.
- `onLoadComplete(target)` increments `loadStep` and invokes the next step
  inline. It does not record/use the target. There is no `onLoadInit` listener.
- Therefore a proposed single mutable “current request” field is not an
  established completion/init association: it can already refer to the next
  request when a later event is observed. Actual callback scheduling is still
  unknown; source order does not prove a native event order.

This rules out promoting a global request counter or the helper-request marker
into the missing binding. Existing `initCtrl` paths and literal boot text remain
ineligible as s268 established. No extra load or gameplay method is invoked.

## Independent read facility attempt

The installed native executable matches the s259 receipt SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
[facility.json](facility.json) retains exact commands, transcript hashes, exits
and measured times. This hash identifies the inspected executable only.

| Check | Observed result | Qualification limit |
| --- | --- | --- |
| `nm -u` on pinned player | Imports include `read`, `fread`, `mmap`, `CFReadStreamRead`, file and HTTP stream creation | No executed read, returned buffer, consumer or request binding |
| Module-scoped LLDB loader-symbol lookup | No matches, exit 1 | No named loader/request/callback resolver found by this query; stripped/native reverse engineering remains possible |
| DTrace read-return probe listing in sandbox | Operation not permitted, exit 1 | No probe listing or events |
| Same listing outside sandbox | DTrace requires additional privileges, exit 1 | Sandbox escape alone does not provide this observation facility |

No player was launched, attached, re-signed or modified. No security settings
were changed. The DTrace result does **not** mean LLDB attachment is impossible;
it is a failure of this particular facility query. The imported APIs also do
not establish which read path this P1 load actually uses. A successful future
OS read alone would still need a loader-consumption and request/target join.
A server response or packet capture alone would establish delivery, not that join.

There are zero new SWF builds/captures. The first qualification prerequisite
remains missing, so an unchanged capture or blind resource swap would not
supply the required discriminator. A fresh paired capture is necessary after
an independent read-to-request adapter is qualified. Future costs are unknown;
actual facility/check costs and the session interval are recorded, not estimated
from event counts. s268's offline byte substitution is not rerun as a runtime
control and is not counted as one.

## Next discriminator, limited to this P1 load

1. In an owned s259-normal-derived process, locate the executed read-return
   call chain among the observed imports (including buffering or mmap if used).
   Capture returned buffers/ranges and read ordering, not just filenames,
   lengths or a precomputed hash. Resolve the consuming loader request from
   the actual native call chain; retain executable offsets and byte provenance.
2. Observe that request's completion target **before** authored `loadStep++`
   and the inline next-step call. Observe initialization separately with the
   same resolved request/target association. Preserve original callback bodies,
   branch order and input tape. Do not infer callback order or use a lone
   global current-request variable. Capture failures and missing reads too.
3. After the normal pair is qualified, actually supply the archived
   instrumented `game/fighter/yihu.swf` bytes for the P1 Yijiao request in a
   separate owned run. Keep the expected Yijiao identity unchanged. Require
   the independent read/request/callback evidence to detect this mismatch,
   regardless of whether the load succeeds or errors. Never alter the original
   resource, historic build/receipt, or expected hash to make it pass.
4. Bound the callback target from request through init and measured use to
   observed unload/replacement. Calibrate retained-target and same-slot
   replacement behavior; path/depth equality, pointer reuse, frame1 reentry and
   self-declared tokens alone are insufficient. Record the actual interval,
   not an invented indefinite lifetime. Keep both complete streams and costs.

Until all four are observed, the fixed-evidence requirement command exits 1.
This slice introduces no accepting trace schema or permissive validator.

## Source-first and scope

The source question answered here is the original request/callback body and
its inline continuation. No authored frame, PlaceObject/MOVE, label exit,
input/random tape, scheduling rule or gameplay mechanism changes. Allocation
and load lifetime, actual native callback order and same-input comparison are
explicitly unproved; the five-question gate authorizes no runtime implementation.

Only s277 evidence, its focused diagnosis tests and requested tracking files
change. Ranks 1–4/6–9, priority documents, s254–s276, strict validators, shared
samplers, production runtime, contracts, thresholds and baselines are untouched.
No broad rollout, receipt repair, self-declared hash, file-hash-as-live-proof,
merge or deployment.

## Reproduce and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s277/diagnose.py --output /tmp/s277.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s277/diagnose.py --output /tmp/s277-required.json --require-loader-attestation # expected exit 1
python3 -m unittest tools.tests.test_loader_read_target_diagnosis tools.tests.test_loader_attestation_diagnosis tools.tests.test_capture_runtime_fighter tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

Exact facility commands are in `facility.json`; these are static queries/probe
listing, not a capture recipe. Repeating them may have different host permission
results and must not overwrite the retained observations. Portable diagnosis
needs neither a player nor DTrace and recomputes the pinned historical stream.
Historical receipt revalidation requires the original paths/player as documented
in [s259](../s259/README.md), without resealing.
[Gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json) and [manifest audit](manifest-audit.json) retain
actual results. No Godot check applies to this evidence-only change.

49 focused tests pass. The unchanged s259 normal receipt revalidates with exit 0;
diagnosis, integrity, handoff and contracts pass. Loader qualification remains
exit 1. Contract command and measured costs are in `project-checks.json`.
