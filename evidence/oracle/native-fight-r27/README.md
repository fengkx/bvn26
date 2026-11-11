# M0-02 r27: independent witness feasibility bound (offline)

Base `75fc1f67bd2714b17bf8633b2868bed9e7d327de` (#270 squash). New branch from that exact commit. Tracked tree initially clean; untracked b97e/c62f directories untouched/uncommitted. No live, player launch, debugger attach, host query, CU, password, permission/security change, production action or historical package edit. Official weekly remaining UNKNOWN.

## Decision

**No ready, independently qualified per-instance removal/dispatch witness was established from the available artifacts.** This is a bounded feasibility refusal, not proof that Flash/debugger observation is globally impossible. No new SWF observer, callback, breakpoint or capture facility is added. The new package only records and tests source/capability bounds; it does not repeat a static sampling rank or expand native disassembly.

## Evidence reviewed

`input-pins.json` binds locked main/yihu source, the physical-PID capture tool, historical debugger receipts and retained s357/s366 bounds. `feasibility.json` includes the unchanged r25/r26 identity refusal and a reproducible lexical source scan. The scan is explicitly limited to exported source/path spellings, not a proof excluding computed property handlers or all native events.

1. Locked main/yihu exports contain no lexical `onUnload` / `onClipEvent(unload)` callback to wrap. Yihu has four explicit unload call sites: AImain.unloadMovie in body638/1180/1672 control initialization, plus a root this.unloadMovie when zhanting is undefined. None is a Sprite16 helper removal callback. AImain is not evidence for instance2915; no logged execution of these calls is tied to the r25 interval. Static RemoveObject2 at a depth remains encoded timeline evidence, not an observed runtime edge.
2. The standard does encode a ClipEventUnload handler event and a depth-addressed RemoveObject2 display-list operation. This documents syntax/format, not the missing native object generation, callback activation or interrupted-goto identity. We cannot infer these from the specification. [Adobe SWF19, CLIPEVENTFLAGS and RemoveObject2, printed48–50](https://open-flash.github.io/mirrors/swf-spec-19.pdf#page=50) (publisher-authored PDF mirror; lookup record in sources.json).
3. Historical r244's exact-owned-process receipt reports attach/register-read/detach success with the pinned player SHA. Historical r245 reports a generic hardware entry stop. Those are real retained capabilities, **not** r25 helper/disposal/dispatcher semantics or current host permissions. Historical r246's independent task_for_pid return5 and failed guest read remain scoped to that attempt; they neither revoke all debugger access nor establish today's permission state. No retry or new denial occurred here.
4. Retained s357/s366 explicitly stop before qualified loaded callback/owner/activation and dispatcher-outcome association. Name/callsite bytes and untyped addresses cannot fill those gaps. These historical bounds are read, pinned and cited only; their inventories/disassembly are not rerun as new progress.

## Routes and why none is a ready witness

| Route | Justified capability | Missing qualification |
| --- | --- | --- |
| Existing source callback | Exported scripts can be inspected | No existing helper unload callback in scanned sources; no native edge receipt |
| Add ClipEventUnload/onUnload | Event encoding is documented | New callback changes the observed event path; native generation/activation binding and preservation unproved; handler emission would not certify dispatcher return |
| Parent/depth/token or polling | Can describe source placement/readback | Reused paths/depths, gaps between samples and object recreation; no independently observed destruction/interrupt |
| Owned native debugger | Historical attach/register/hardware stop succeeded | No source-bound removal/dispatch address, owner/generation/activation schema or matching outcome; present permissions and observer preservation untested |

A new unload handler would be a separate source event, but adding it would not by itself make its identity/output independent of the VM/event machinery under investigation. Without independently established binding and observer off/on preservation, declaring it a per-instance native witness would be speculative. We therefore do not compile an unload observer merely because its syntax exists.

Similarly, a source-generated generation counter or root mailbox could name observer activity but cannot certify native lifetime continuity or which native dispatch edge caused the body target. Another installation is not destruction; the last path observation is not a death timestamp. A debugger's return-address-looking value or arbitrary stop is not a matching outer return. No pointer/timestamp identity shortcut is admitted.

## Exact prerequisite to reopen facility work

Before another capture/observer, obtain a reviewable offline binding proposal identifying **one specific removal or dispatch boundary**, the receipt-pinned player bytes/symbol provenance, and an independently justified object-owner/generation/activation schema. It must state which fields bind the initiating helper and which separately bind the body target, cover replacement/reuse and missing/repeated/interleaved callbacks, and distinguish event entry from actual destruction, interruption or dispatcher exit. It must also specify observer off/on preservation and bounded owned-process cleanup without permission/signature changes. Existing rendering-function stops do not supply this proposal.

This prerequisite is presently missing; the package does not select a speculative address or authorize new attachment/live. Independent review should decide whether to commission that distinct semantic-binding research. If no supported binding can be supplied, keep the native-lifetime requirement blocked rather than repeat r25 or add another source-only after marker. Later live is conditional on a justified, reviewed discriminator and separate authorization, not the automatic next action.

## Admission and verification

All five flags false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending. r26's body-target-observed-dispatch-identity-unjoined/cause=unproved remains. No native return, helper liveness, removal edge, causal join or after-silence diagnosis. Both analyzer modes exit1 with unchanged `Incomplete actor state at clock boundary`; the original ten incomplete boundaries are not trimmed or filled.

Five tests check scoped source scanning, distinction between explicit calls and callbacks, historical capability versus current permission/semantic readiness, synthetic capability success without admission, and retained structural refusal. No new SWF compile is warranted because no instrumentation is added. checks.json records tests, verify.py, check_handoff.py and git diff --check.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r27/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r27/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r27 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```
