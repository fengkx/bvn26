# M0-02 r29: independent public debugger-protocol semantic research

Base `40127e46a9bf16e9aa0977dd33fd60251ef6d9e2` (#272 squash). New branch from the exact supplied detached HEAD. This is distinct external-source research, commissioned through the repository research skill to a background researcher and independently checked by the parent. No old sampling rank/disassembly was advanced or counted as progress. No Flash/CU, debugger socket/attach, Java/C++ compilation, protocol command or new capture/observer implementation. Historical oracle packages and untracked b97e/c62f leftovers untouched. Official weekly remaining UNKNOWN.

## New evidence found: protocol semantics, not yet native semantics

[protocol-research.md](protocol-research.md) cites the Apache Flex SDK's public source at commit `ba414443032b49c45ff11b61db452c8a8f428bd8`. It establishes a **specific client-side protocol lead**:

- `InPlaceObject=13` and `InRemoveObject=4` are enumerated player-originated messages. The client decodes placement as an object ID plus path and removal as an object ID. The corresponding object-bag updates are commented out; inspecting standard API events alone would not retain these decoded records.
- `Value.getId` defines object-alias semantics; `Session.getValue` promises ID stability during the Value's life. Its null result can mean out-of-scope/unavailable, not native destruction. AS2-specific pseudo-values demonstrate legacy API scope; they do not establish support in the exact pinned Flash32 build.
- `Frame` is valid while suspended. Incoming constructor thisId is discarded, and cross-suspension frame matching uses call signatures heuristically. These client identities cannot certify a native activation generation.
- Client initialization sends options, including script-stuck behavior changes. It must not be described as a passive, preservation-neutral connection.

These are independent primary-source meanings that were absent from r26–r28. They supply a focused wire/API investigation route, **not** a pinned-player native address or verified owner/generation/activation layout. No producer-side implementation or emitted message for r25 has been obtained; no message-ID integer is treated as a code address. Pointer-width decoding is a wire-format fact, not proof that the ID is a safe native object pointer.

## Separate public VM-source route checked

The inspected avmplus source at commit `65a05927767f3735db37823eebf7d743531f5d37` explicitly defines its scope as AVM2/AS3 and ABC programs. MethodEnv exposes method/scope members within that source. Those declarations cannot be transplanted as the proprietary player's AVM1 helper layout or matched to Flash32 field offsets by similar names. [AVM2 introduction](https://github.com/adobe-flash/avmplus/blob/65a05927767f3735db37823eebf7d743531f5d37/doc/avmspec/intro.dox#L4-L30), [MethodEnv declarations](https://github.com/adobe-flash/avmplus/blob/65a05927767f3735db37823eebf7d743531f5d37/core/MethodEnv.h#L235-L244).

The original Adobe/Mozilla Tamarin FAQ explicitly scoped that historical release to AVM2 rather than AVM1. This is a statement about that release, not a claim that no AVM1 source/symbol evidence can ever exist. [Historical project FAQ](https://www-archive.mozilla.org/projects/tamarin/faq).

## What can be justified next, without connecting anything now

A concrete follow-up is a **producer/version qualification study** for the placement/removal message family: establish whether the pinned Flash32 AVM1 implementation emits it for timeline helper placement/removal, under which debug/negotiation conditions, and whether IDs share the Value API namespace. Determine producer ordering, dropped/coalesced messages, reuse after end-of-life and parent-definition/depth scope before proposing a join. Consumer code alone answers none of these.

Before any separately authorized protocol experiment, audit the exact connection/initialization commands and debugging requirements of the locked movie. The reviewed plan must account for suspension, getter/frame requests and script-stuck/fault options; ordinary FDB attachment is not an approved zero-change baseline. No new capture tool or command whitelist is implemented here, and this document does not authorize opening a socket, adding debug metadata or changing locked assets.

If producer evidence later qualifies these messages, they could support observed protocol-level placement/removal IDs and bounded alias checks. They would still need independent generation/reuse and dispatch-edge qualification to identify the r25 helper/activation, and independent preservation controls. They would not automatically prove native destruction, interrupt semantics, dispatcher return, target→call association, global ticks, OS input join or noninterference. If producer qualification fails or remains unavailable, retain that specific limitation instead of treating missing API events as absence of removal.

## Reproducible research artifacts and scope

`source-receipts.json` pins exact public commits, original paths/URLs, decompressed SHA256 and line counts. `public-sources/` contains compressed, unmodified licensed source snapshots as evidence, plus upstream Apache LICENSE/NOTICE and MPL license (license-text copies have trailing whitespace removed; all license wording retained). Headers are retained; sources are not linked into or executed by the product. Temporary download failures for guessed optional avmplus documentation paths were not treated as absence of implementation; positive retained source is the evidence.

`analyze.py` reads these local snapshots, validates hashes and static source anchors, reports the new protocol facts and keeps all native mappings null. It is not a protocol decoder/client or runtime observer. `findings.json` is a research report, not an execution receipt. Tests run offline and require no network or player.

Only the old full-prefix structural gate is replayed as a regression check (two pinned r25 inputs). That exit1 is explicitly **not new semantic-binding evidence**. Both CLI modes exit1; Incomplete actor state at clock boundary remains. All five flags false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending. No native return, lifetime, removal edge or after-silence cause has been proved.

## Validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r29/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r29/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r29 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

Seven tests cover actual message values with no native promotion, snapshot tampering, changed client retention, missing protocol declarations, limited ID/frame semantics, AVM2 mislabeling and non-passive initialization. checks.json records results. Stop after Draft for independent review; no live follows automatically.
