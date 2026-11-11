# M0-02 r31: bounded producer search and response/reset qualification refusal

Base `9e709a34a9f9f64abe2f2ca9842fcc26576b0e32` (#274 squash), branch `feat/m0-02-oracle-r31-research`.

Classification: **producer-contract-unavailable-response-and-reset-qualification-refused**. Here unavailable means **not obtained within the documented search**, not globally absent or impossible.

## New evidence, with its limits

[producer-search.md](producer-search.md) records independent first-party research and its search ledger. The pinned client names specific producer files (`core/debugtags.h`, `core/playerdebugger.cpp`, and `playerdebugger.h` atom definitions); these are concrete provenance targets, not the implementations. An Adobe February 2013 AS2 manual distinguishes debugger display-list removal from retained watch visibility and says playback continues after ending a debug session. This is a historical UI contract, not Flash32 lifecycle emission, ID reuse or option reset. The exact downloaded PDF hash/pages are in `adobe-doc-receipt.json`; the complete PDF remains outside the repo. A public GitHub tree request returned HTTP403, explicitly retained as a search limitation, not repository-absence evidence or an approval denial.

[response-review.md](response-review.md) adds a distinct implementation review to r30:

- Response acceptance uses a message-type/isolate counter increment; it does not itself bind a unique request, echoed name/value and effective state.
- InOption writes a name-keyed cache; getOption reads it after the counter wait. The set wrapper discards the response boolean. This does not prove any response mismatch occurred; it prevents promoting an acknowledgement/cache read to a verified restoration transaction without producer semantics.
- InProcessTag automatically triggers OutProcessedTag. Preservation review must include incoming-triggered replies, not merely initialization/timeout traffic. Whether the exact player requires or emits this message is unproved.
- Local disconnected/InExit handling does not attest effective option reset. No reset/persistence claim is inferred.

The tracked-text lookup in `retained-search.json` found protocol-name hits in research material; it did not discover a qualifying producer transcript. This search excludes binary/compressed contents and is not an exhaustive absence proof. The existing pinned r29/r30 snapshots were read directly. Historical r25 structural replay is only a regression check and is not new semantic evidence.

## Qualification outcome

No exact Debugger32.0.0.465 producer lifecycle emission, placement/removal-to-Value ID namespace equivalence, allocation/reuse generation, owner/activation mapping, effective option state or reset semantics was qualified. No native boundary/address, native return, helper lifetime, call association or after-silence cause is inferred. A behavior-preserving connection remains unproved. AVM2 layout is not used as AVM1 evidence.

All five flags remain false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending. Both analyzer modes exit1 with the existing `Incomplete actor state at clock boundary` refusal. Nothing was trimmed or filled.

## Reproducibility and scope

`source-receipts.json` pins the new DMessageCounter source snapshot at the same Apache Flex commit as r29/r30; original license/notice wording is retained. Other source snapshots are reused read-only. `analyze.py` checks source hashes and narrow reviewed anchors; it is not a Java interpreter, protocol client, connection planner or exhaustive producer analysis. `test_response_review.py` checks changed counter/cache/reply rules, hash corruption and non-promotion. `findings.json`, `checks.json`, and `artifact-sha256.json` retain report/check/package identities.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r31 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r31/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r31/analyze.py --require-oracle
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
git diff --check
```

No live, FDB attach, player connection, Java/C++ execution, SWF compile, breakpoint/observer/driver, Computer Use or deployment operation. Historical packages, locked game/scripts, and the untracked r22 failed directories remain unchanged. Official weekly remaining UNKNOWN.

## Next prerequisite, not an automatic next slice

Seek authorized exact-build producer definitions/handlers or equivalent version-bound documentation for the named source targets. It must cover lifecycle emission conditions, ID namespace/reuse, option response identity/effective values, progress acknowledgements and disconnect/reset. A qualifying already-retained producer transcript could support only the fields and edges it actually observes. If these sources are unavailable, stop this route rather than repeat client inventories. Any later connection experiment requires separate preservation review and explicit authorization; none is designed or authorized here. Stop after Draft PR for independent review.
