# M0-02 r30: producer/version/namespace qualification and preservation review

Base: `0e1cdfe55df524de898779c163e64ca8d23880bf` (#273 squash). Branch: `feat/m0-02-oracle-r30-qualification`.

Classification: **client-contract-qualified-producer-namespace-and-preservation-unproved**.

This is distinct offline qualification of the r29 public protocol lead, not a reranking of r25–r28. It qualifies a narrower client implementation chain and identifies additional barriers to producer identification and preservation. No new native address or instrumentation is proposed.

## What was actually qualified

[protocol-qualification.md](protocol-qualification.md) traces commit-pinned Apache Flex client code:

- MovieClip atom `getPtr` → Long → isolate-scoped value lookup/cache → `DValue.getId`. Cache insertion excludes HAS_GETTER. This is an implementation link for **decoded value atoms**, not a producer-side link to placement/removal IDs.
- InVersion decodes one integer plus optional pointer width (fallback four); it does not attest a complete player build, executable hash, movie PID or AVM mode. Pointer width is class-wide static state. No wire version/width was observed here.
- The inspected accept path does not authenticate the peer as the pinned movie. bind's squelch response and capability queries do not substitute for producer attestation.
- Continue rotates client value caches and invalidates frame views; cache absence is not destruction or allocation generation.
- Conditional receive-timeout heartbeat sends squelch. A client left idle is not necessarily receive-only.

[preservation-review.md](preservation-review.md) inventories the ordered initialization sends, option values and missing original-state/restore obligations. Bind performs adjustments and starts background work before its version-failure check. Reviewed unbind sends OutExit and closes the connection without an explicit option-restoration sequence; player-side reset is unknown. Review status: **not-qualified-for-behavior-preserving-connection**. Static review itself changed no player state.

## What remains unproved

The intended producer remains the historically pinned Flash Player Debugger 32.0.0.465, x86_64/Rosetta, executable SHA256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be` ([existing environment record](../../reference-environment.md#runtime)). That historical executable identity is not evidence of a protocol producer session: there is no retained qualifying handshake or placement/removal transcript supplied by this research. The public client commit is pinned, but no debugger binary built from it was executed or qualified against that player.

No producer implementation/version contract or receipt establishes AVM1 helper emission, lifecycle-ID/Value-ID namespace equivalence, allocation reuse/generation, parent-definition/depth binding, activation identity, or delivery/order/loss semantics. No source code layout from AVM2 is transferred to AVM1. No native boundary/return, helper lifetime, initiating-call join or cause of after-silence is proved.

All five flags remain false: production_admitted, native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending. Existing structural refusal is replayed only as a regression, not new evidence: **Incomplete actor state at clock boundary**, both analyzer modes exit1.

## Artifacts and checks

- `source-receipts.json`: three additional unmodified gzip snapshots at Apache Flex commit `ba414443032b49c45ff11b61db452c8a8f428bd8`, SHA256/URLs. Existing source snapshots are reused read-only from r29. Apache license/notice copies retain wording (r29 whitespace normalization retained).
- `analyze.py`: offline source-hash/initialization/ID-chain audit and explicit refusal report, not a protocol implementation. It does not claim exhaustive Java analysis or producer verification.
- `test_qualification.py`: negative source-change tests and refusal checks; no synthetic event is passed off as a player receipt.
- `findings.json`, `checks.json`, `artifact-sha256.json`: report, executed check results, package hashes.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r30 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r30/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r30/analyze.py --require-oracle
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
git diff --check
```

No live, FDB attachment, socket/player connection, Java/C++ execution, SWF compile, Computer Use, callback/observer/driver, asset/runtime change, or deployment operation. Historical packages and untracked b97e/c62f directories remain untouched. Official weekly remaining UNKNOWN.

## Exact next prerequisite

Obtain independent **producer-side** documentation/source or already-retained protocol evidence bound to the exact player/version, covering lifecycle emission conditions and ID namespace/reuse. Also resolve initialization, background/timeout traffic, effective prior values and disconnect/reset semantics before any preservation-neutral connection can be proposed. A new client based only on consumer guesses is not justified. If such evidence is unavailable, keep this route unqualified; any later experiment needs a separately reviewed preservation plan and authorization. This package neither authorizes nor schedules live. Stop after Draft PR for independent review.
