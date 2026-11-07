# s334 — AFTER-s326 rank #8: AImain allocation

Base: `1396401a60af3b553a240ac353ee8b6d34840e61` (s333 #211).
Branch: `feat/s334-aimain-allocation`.
Authority: [unchanged AFTER-s326 rank #8](../next-fix-priority-after-s326.md).
Only rank 8 is executed. Ranks 1–7 delivered as s327–s333 stay closed;
rank 9 remains planning. `production_admitted=false`; `native_parity_proven=false`;
M0-02 pending; zero product obligations closed.

## Result and evidence boundary

Separate byte-bound parent/depth and saved-reference lookup paths were **not
derived**. This is an honest prerequisite-gap delivery, not native allocation
mechanism completion. No independent native observation was obtained. Actual
clearing/replacement/free/reuse and uninterrupted pool generations remain unproved.

[Diagnosis](diagnosis.json) reproduces the entire locked s325 diagnosis, including
its recursive retained evidence, and extracts exact line spans/source for three
retained adapter functions. None is invoked by this audit:

| Inspected function | Source-observable boundary |
| --- | --- |
| s279 `pin_imports.pin` | Reads Mach-O bytes and maps four imported allocator stubs to indirect pointer slots. Those slots are neither parent/depth occupants nor saved AS2 references. No pool checkout/return ledger is implemented. |
| `probe_owned_debugger.debugger_script` | Reads selected frame-zero CPU registers and detaches. No display-slot lookup, saved-value decoding, object layout or generation resolver is implemented. |
| `probe_owned_debugger.probe` | Owns a PID/build, waits for an AIREF profile after launch, and invokes extension hooks. Process custody and hooks supply neither lookup path nor pre-allocation uninterrupted pool coverage. |

These are bounded source inspections, not fresh live facts or an exhaustive
search of machine code/facilities. They do not prove a resolver cannot be built.
The s325 symbol counts, import byte pins, historical 8,290 AIREF events, operand
comparisons and source bounds are **retained validation only**, never new progress.
There is no new binary disassembly or candidate resolver address in this slice.

## Separate unresolved paths and ordering

[diagnose.py](diagnose.py) keeps two distinct unresolved records:

- Parent/depth: independently bind the parent instance generation and depth to
  the current display-list occupant using instruction bytes and layout evidence.
- Saved reference: independently locate and decode the saved AS2 value into its
  referent using its own byte-bound dereference path. Do not copy the slot result.

Both module-relative addresses, instruction bytes, layouts, live bindings and
result allocation generations remain null. Disk module identity is not loaded
module/owner identity. Only after both paths are qualified may a live observer
start before control allocation and remain uninterrupted through actual retained
content clearing, same-name/depth replacement, free and reuse. Pool generations
must include internal checkout/return and deferred-free ordering. Removal need
not free immediately; absent or unexercised reuse remains unproved.

No imported allocator as pool coverage, pointer-only identity, 0→1 alias,
property deletion as clearing, token-loss inference or unloaded exemption.
No hypothetical native trace, proof override, guessed offset or accepting resolver
is supplied. All native controls are deferred, not failed observed experiments.

## Gates and reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s334/diagnose.py --output /tmp/s334.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s334 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnosis exit 0 means reproducible package consistency only. Each of
`--require-slot-reference`, `--require-content-clearing`, `--require-replacement`
and `--require-allocation-identity` exits 1 with a distinct `S334_*_UNPROVED` code.
Changed pinned inputs emit `S334_EVIDENCE_INVALID`. Tests reject changed adapters
and prior evidence, keep the paths separate and null, and exercise every CLI gate.
Retained s325/s316/s307/s298/s289 and shared AImain/display/sampling tests are rerun.
Actual exits and timings: [gates](gates.json), [project checks](project-checks.json)
and [session timing](session-timing.json). Green package checks do not prove parity.

## Source-first and scope

1. Locked s325 → s316 → s307/s298/s289/s261 retains Yijiao Sprite455 frame1
   initCtrl unload, Sprite3 frame1 stop and no frame2 DoAction.
2. Retained parent placement is unchanged; no new native lifetime is observed.
3. No invented label-end return or scheduling change.
4. Tests protect custody/unknowns, not hypothetical allocation behavior.
5. Historical same-input AS2 evidence is retained; no new original/Godot comparison.

Only s334 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
Authority, s254–s333, game/scripts, runtime, contracts and shared tools remain
byte-identical. Zero builds, launches, attaches, live memory reads or captures.
No re-ranking or other-rank execution. [Scope](scope-audit.json),
[manifest changes](manifest-audit.json), [input pins](input-sha256.json) and
[artifact hashes](artifact-sha256.json) preserve custody. Artifact index excludes
itself and caches. Measured packaging/check time excludes initial reading/design
and subsequent commit/push/PR work; person-days unknown. Draft only; no merge,
ready marking or deployment.
