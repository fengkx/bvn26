# s268 — Runtime loader attestation (unproved)

Base: master `b0fa64b8` / #145; branch `feat/s268-loader-attestation`.
Exclusive authority: [AFTER-s263 rank 5](../next-fix-priority-after-s263.md).
`production_admitted=false`; `native_parity_proven=false`;
`loader_attestation_proved=false`; M0-02 stays pending.

**Evidence-only diagnosis. No actual load→consumed bytes→instance lifetime
contract is proved. The actual wrong-resource load control remains missing.**
The offline byte-substitution negative below is explicitly not that control.
No runtime implementation or receipt repair is justified by these results.

## Retained evidence and new bounded audit

[diagnose.py](diagnose.py) pins and audits the original s259 normal/held and
s263 archives, complete captures, metadata, receipts and loader source. It checks
all archived output hashes against build metadata AND historical receipt entries,
all locked source hashes, and the full raw trace hash/sequence using the unchanged
capture validator. For s263 it overlays the archived s263 extension on s257
in memory. It does not extract over historical files or reseal receipts.

| Capture | Complete events | Original receipt revalidation | Actual callback/bytes/lifetime join |
| --- | ---: | --- | --- |
| s259 normal | 5,503 | exit 0 | missing |
| s259 held | 5,416 | exit 0 | missing |
| s263 | 9,774 | exit 0 | missing |

[diagnosis.json](diagnosis.json) records exact request/callback source, all event
kind counts, candidate proxy rows, source and instrumented hashes separately,
and missing observations as `null`. It is a prerequisite audit, not a new
sampling result or a claim that all gameplay/dimension gates pass.

The narrow target for a subsequent experiment is s259 normal P1 Yijiao:
`scripts/main.json#DefineSprite_1900/frame_1/DoAction.as`, `loadman("p1")`,
`_this._loader.loadClip(_root.fighterDir + _loc3_.url,_root.game[pr])`.
The real authored `LO.onLoadComplete(target)` only increments `loadStep` and
calls the next step. It neither consumes nor records `target`; its presence in
source does not prove a particular callback happened in the capture.

The archive audit exposes three unsuitable identity proxies:

- `helper_load` is emitted inside `loadfz` **before** `loadClip`. It observes a
  request for a helper, not the fighter callback or completed instance.
- `initCtrl` records a path, not independently consumed bytes or a lifetime
  generation. Later same-path use cannot establish continuous identity.
- `boot` retains the literal `vs_com,minren,yihu,AI=5` even for these Yijiao/Chad
  cases. It is bootstrap text, not a live fighter identity measurement.

Both retained capture environment outputs explicitly have `runtime_fighter=null`.
`capture_native_player._verify_runtime_fighter` returns `None` for these static
cases. Its dynamic-case file/path checks would still be build provenance, not
an observation of a loader callback's live referent. We do not enable that path,
promote its name to an attestation claim, or change the strict adapter.

## Wrong-resource negative and its boundary

The bounded offline control feeds archived **instrumented Yihu bytes** to the
expected **instrumented Yijiao hash** from the same s259 normal build. Correct
bytes pass; substituted bytes reject with `wrong resource bytes`. Both hashes
and exits are in `diagnosis.json`. No original resource, archive, capture, tape
or receipt is modified. Tests also reject changed bytes and changed callback
source rather than silently reusing the old conclusion.

This proves only that the archived-byte comparison discriminates the two files.
**No player loaded the substituted resource.** A build hash check cannot detect
or exclude a different resource being consumed by a live load unless the read
and target are independently observed. Therefore the actual wrong-resource
runtime negative remains `null` and the attestation gate remains exit 1.

## Why no new capture, and next discriminator

This slice makes zero new builds/player launches. Repeating the unchanged
capture cannot recover unrecorded callback arguments; adding a path or embedded
self-declared hash alone would still not establish consumed bytes. No independent
load/read-to-target observation adapter has been established in these retained
artifacts. This is a bounded evidence limitation, not a claim that such an
adapter is impossible. New capture is required to resolve the contract, but no
AS2-only proxy run is presented as that resolution. Measured audit/check costs
and session interval are retained; no hypothetical capture cost is reported.

1. Extend only the s259 normal P1 request and existing MovieClipLoader listener.
   Record request identity, callback target and callback order without moving
   `loadStep`, changing predicates or invoking extra gameplay methods. Observe
   initialization separately; do not equate completion with initialization.
2. Establish an independent observation of the actual resource bytes consumed
   by that load, tied to the same request and callback. A configured URL,
   pre/post build hash, byte count or self-declared token is insufficient. Preserve
   source→instrumented output provenance as a separate relation.
3. Observe that callback target through initialization and bounded use until
   unload/replacement. Distinguish repeated loads at the same path/depth from
   retained lifetime; do not mint identity from frame1 re-entry or path equality.
4. In a paired owned run, actually supply a different locked resource to the
   same requested target while retaining the expected resource identity. Record
   the consumed bytes, success/error callback, target and lifetime. Require the
   mismatch to reject; do not alter the expected identity to make it pass.
5. Retain both full streams and controls. Missing read/callback/lifetime events
   keep the gate red. Only that proved bounded contract can justify a future
   implementation; never retrofit historical `runtime_fighter` fields.

## Source-first boundary and exclusions

The source path, request and callback are verified against the locked bundle
and all three archived loader patches. No authored frame, PlaceObject/MOVE,
label exit, scheduling order or gameplay mechanism changes. Instance placement
and load lifetime are explicitly unresolved rather than inferred from the
existing geometry/AS stamps. No same-input original comparison is newly claimed.
The five-question source-first gate therefore authorizes no runtime change.

Only s268 evidence, its focused test and requested tracking files change.
Ranks 1–4/6–9 and s254–s267 remain untouched, including priority documents.
Production runtime, shared samplers, strict validators, contracts, input/random
tapes and thresholds are unchanged. No parity/product obligation closes.

## Checks and reproduce

[Gates](gates.json): portable diagnosis exit 0; loader requirement exit 1;
three unchanged historical receipts exit 0; 43 focused tests pass.
[Project checks](project-checks.json) retain integrity, handoff and contracts
commands/exits/timings. [Scope audit](scope-audit.json) records the allowed diff;
[manifest audit](manifest-audit.json) records only changed tracked-file hashes.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s268/diagnose.py --output /tmp/s268.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s268/diagnose.py --output /tmp/s268-required.json --require-loader-attestation # expected exit 1
python3 -m unittest tools.tests.test_loader_attestation_diagnosis tools.tests.test_capture_runtime_fighter tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Portable diagnosis/tests need no player or cache. Full historical receipt
revalidation uses the original receipt paths and pinned executable; restore
archives as documented in [s259](../s259/README.md) and [s263](../s263/README.md),
then use exact commands in `gates.json`. Do not reseal a receipt if its environment
is unavailable. No merge or deployment.
