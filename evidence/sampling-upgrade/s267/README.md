# s267 — AImain allocation identity across clearing (unproved)

Base: master `ddd23ad9d37333ba51a640d0f87dbd22de221825` / #144.
Exclusive authority: [AFTER-s263 rank 4](../next-fix-priority-after-s263.md).
`production_admitted=false`; `native_parity_proven=false`;
`mapping_fix_proved=false`; M0-02 stays pending.

**This is an evidence-only prerequisite diagnosis. The requested native
allocation-generation observations and calibrated retained-content-clear /
same-depth replacement pair have NOT been established.** No mapping is
implemented and no product obligation closes. Missing measurements are `null`,
never generated from an AS2 path, token, callback counter or frame number.

## What this slice adds

The portable [diagnosis](diagnosis.json) revalidates the locked s261 capture,
source exports and compiled instrumentation through its unchanged analyzer.
It exposes the precise native observations missing at each existing site and
separates the two control requirements. Historical s261 files are not copied
into replacement baselines or resealed.

| Retained s261 site | Event / root | Frames | Native address / generation / saved-reference referent |
| --- | --- | --- | --- |
| Last nonzero observer | 36 / 8 | 1/2 | unobserved / unobserved / unobserved |
| First zero observer | 44 / 9 | 0/0 | unobserved / unobserved / unobserved |

These are observer boundaries, not the exact clearing instruction. The parent
retains its source placement between frames 1/2; that does not exclude an
internal native replacement. All 8,290 events and 61 display samples are retained.
The existing 122-row / 14-field comparison with s255 still passes; this is a
recomputation of historical evidence, not a new capture or native/Godot parity.

| Required control | Available s261 evidence | Still missing |
| --- | --- | --- |
| Retained object with content cleared | Explicit deletion of one token property; AS2 reference/token signal `true,false` | Independently verified native object retention across actual content clearing, with complete allocation/free history |
| Same name/depth replacement | Explicit remove/create; the same AS2 signal `true,false` | Native allocation generations before/after, including address reuse, and resolution of the saved reference |

The property-deletion control is **not** promoted to the requested
retained-content-clear control. The known remove/create operation is **not**
promoted to a measured native generation transition. Identical AS2 signals
cannot select between these alternatives.

## Native observation facility audit

A bounded, read-only [executable audit](facility/audit.json) pins the exact s261
player SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`:

- `nm -U` exposes six defined symbols, none a MovieClip/slot/allocation resolver.
- `dwarfdump --debug-info` lists no debug information entries.
- Module-scoped LLDB lookup of `MovieClip|Sprite|unloadMovie|ScriptObject`
  returns no matches, exit 1. It does not inspect unrelated system modules.

This establishes the result of those queries, **not that native observation is
impossible**. The repository already has [successful same-binary attachment](../../importer-loud-fail/r244/retry/debugger/feasibility.json)
and bounded debugger tooling. Its arbitrary-stop registers and the
`probe_owned_source_call.py` composition callsite do not identify this AImain
object, its allocator, destructor, slot resolver or saved-reference binding.
No existing native slot-to-allocation adapter was established for these sites.
An exploratory unrestricted LLDB lookup also matched Foundation's unrelated
`NSScriptObject*` symbols; those are excluded by the retained module-scoped
query. The initial executable basename lookup omitted `Debugger` and failed;
all retained checks use the receipt's exact binary path and hash.

No new player launch, live attach, trap, memory scan, signing or security change
was performed. A fresh AS2-only capture would repeat the already ambiguous
signals without supplying allocation observations. Accordingly this slice
reuses the locked capture and records a failing identity prerequisite rather
than spending a new capture on another proxy. The static facility audit is a
bounded extension, **not** the requested native lifecycle capture.

## Explicit next discriminator

1. Identify and byte-pin the native depth-slot resolver and returned object
   layout for this executable. Establish how the saved AS2 MovieClip reference
   resolves to a native referent separately from the current depth occupant.
   Generic rendering/composition entry points are insufficient.
2. Build an external native allocation/free ledger starting before control
   creation. A generation must come from observed allocation/lifecycle events;
   pointer equality without free/reuse tracking is insufficient. Qualify the
   ledger using both a retained-object content-clear operation and explicit
   same-name/depth replacement. Verify retention from native lifecycle events,
   not from the operation name or missing properties.
3. Observe that same ledger at the equivalent s261 last-nonzero / first-zero
   source sites in one owned run, including the parent slot and saved reference.
   Do not assume a new instrumented capture will clear at numeric roots 8/9;
   preserve the last-nonzero/first-zero boundaries and their real event order.
4. Retain full trace, controls, executable/source/adapter hashes, resolution
   provenance and allocation/free ordering. Missing events or an uncalibrated
   control keep the identity gate red. Even a proved identity discriminator
   would not by itself justify mapping frame 0 to 1 or exempting unloaded nodes.

No future accepting trace format or generic validator is introduced here.
`--require-allocation-identity` intentionally exits 1 on this fixed evidence;
editing a report flag cannot convert missing measurements to proof.

## Source-first scope and exclusions

The unchanged s261 analyzer verifies the exact Yijiao Sprite455 frame1
`initCtrl` unload, Sprite3 frame1 `stop()`, no frame2 DoAction, and the retained
parent placement. Its archived source/timeline/observed boundaries answer the
source questions for the diagnosis; no new runtime behavior is inferred.
Tests assert actual retained boundary/control facts and the missing native
observations, not a guessed object-lifetime model.

Only s267 evidence, one focused test module and tracking change. Ranks
1–3/5–9, s254–s266, production runtime, shared samplers, strict validators,
contracts, input/random tapes and thresholds are untouched. No 0→1 alias,
unloaded exemption, property-loss identity, broad binding, masks/camera,
other AImain families, gameplay change, merge or deployment.

## Gates, cost and reproduction

[Gate results](gates.json): diagnosis and retained receipt exit 0;
allocation identity and full display exit 1. Full display still has **169**
source obligations. Focused tests and [project checks](project-checks.json)
record commands, exits and measured subprocess durations. No new build/capture
cost: zero launches; static audit timings are in `facility/audit.json`.
Session interval is recorded in `session-timing.json`; no person-days inferred.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s267/diagnose.py --output /tmp/s267.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s267/diagnose.py --output /tmp/s267-required.json --require-allocation-identity # expected exit 1
python3 -m unittest tools.tests.test_aimain_allocation_identity tools.tests.test_aimain_content_clearing tools.tests.test_aimain_unload_identity tools.tests.test_display_source_frame_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_display tools.tests.test_display_completion_default tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Portable diagnosis/tests need no player or XML cache. Receipt/full-display
commands use the unchanged s261 paths: restore its build archive, capture log
and receipt plus XML exports as described in [s261](../s261/README.md), then run
`gates.json`. Do not reseal historical receipts. Optional static audit on the
pinned installed player (fresh output directory):

```sh
python3 evidence/sampling-upgrade/s267/audit_facility.py --binary '/Volumes/Flash Player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output /tmp/s267-facility-new
```
