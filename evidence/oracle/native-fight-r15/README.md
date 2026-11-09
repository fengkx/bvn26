# r15: live source consumer observations, true branch refused

One authorized native run from master35b19a9c (#257), **84.5249 seconds**,
movie PID **26153**, tag **m002-r15-live-20261110-c92e**. Physical menu→Vs Com→
一护/Naruto and0.5s fight-J completed. No second run, focus/TCC/human blocker.
Pre-activation frontmost PID21273; all17 subsequent sampled probes show26153.
Sampling does not prove continuous focus. Owned cleanup left no movie PID;
original assets and all75 copied hashes, main+yihu included, passed recheck.

All five flags remain false: production_admitted, native_parity_proven,
oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 pending.
Official remaining UNKNOWN; not claiming above floor.

## Consumer marker facts

7,992 contiguous tagged events include:

| Event | Count |
|---|---:|
| consumer-query-before |224|
| consumer-predicate-result |224 (223 false,1 true)|
| consumer-goto-before |1|
| consumer-goto-after |**0**|
| fight-key-return |2,662 (2 true, both yihu-decision-9)|
| decision-installed |13|
| camera pairs / timer pairs |740 /24|
| actor-state |3,064|
| startFight entry/state-written/exit |1 each|
| menu before/after/exit |2 each|

All observed consumer markers name **doAllAction**; no doStand consumer interval
was observed. This is no proof that doStand is globally unreachable.

The strict join validates **223 false-predicate source intervals**. Each has one
prior observed helper installation, a new consecutive helper-local serial,
non-AI/unpaused matching body-owner key query sequence, matching full predicate
result and no goto markers (as the original false branch requires). No global
tick or physical OS event is assigned by this result.

Validated helper path/local serial ranges:

- /game/p1/mc/instance2553:1–33
- /game/p1/mc/instance2837:1–12
- /game/p1/mc/instance2901:1–141
- /game/p1/mc/instance3027:1–37

These are observed path/serial intervals, not certified lifetime identities.
No interval is accepted based on timestamp proximity or serial alone.

## True branch failure retained

The remaining candidate is **refused**, not a successful consumption/goto join:

- seq6973: query-before, helper instance2901, local serial142, doAllAction,
  body /game/p1/mc, non-AI, getTimer77681/camera ordinal666.
- seq6974–6977: the four nornalhit query sites are present in the raw log.
- seq6978: actual full predicate result true.
- seq6979: original branch's goto-before marker.
- **No goto-after marker exists in the entire capture.** Later helper installation
  and other events occur before the next query. The candidate remains refused;
  its subsequent collected key rows are explicitly `key_join_status=not-joined`.

The second positive key query at seq7043/getTimer77981/ordinal675 is not associated
with a validated consumer interval. We do not infer that the original goto
completed, that helper removal caused the missing log, or that a downstream action
executed from these partial events. The cause requires separate evidence. No
missing return is synthesized; no second capture was launched to replace failure.

## Inherited markers and gates

startFight seq3073→3080 passed unchanged r12 shape checks: zhanting true→false,
menu flag false→true, visible=false; readying already false at entry. Loader,
chushi, timer, actor and all early loading rows remain retained. **12 timer
boundaries contain incomplete HP.** The unchanged r05 structural check on the
entire prefix still refuses `Incomplete actor state at clock boundary`.

Both analyze and --require-oracle exit **1**, even though false source intervals
are descriptively validated. The five admission/synchronization flags remain false.
The new consumer join checks actual short-circuit site order (9 then, as required,
10/11/12), actual booleans, matching body and non-AI/unpaused fields, helper-parent
relation, predicate result and original goto boundaries. Missing/interleaved/
reinstalled/duplicate or gapped invocation candidates are refused; raw failures
and orphans are retained, not trimmed. Timer/camera events are not used to invent
a consumer-global tick. A source-continuation marker would not itself prove native
dispatcher return or later-frame action execution either.

`analyze.py` verifies build/session identity, fresh exclusive raw-tag selection,
contiguous sequence, append interval, physical input PID returns, owned cleanup,
all retained copy hashes and exact tag changes. `observations.json` retains full
marker/candidate outcomes. Tests include false/true synthetic shape, missing
post-goto, reinstall/interleaving, owner/AI/pause/site mismatch, repeated serials,
incomplete short-circuit queries, unrelated keys and raw/build receipt tampering.
Synthetic successful shapes do not become live evidence.

## Receipts / recheck

run-01 retains session, exact-PID AX/CG probes, input ops, nine screenshots,
prelaunch/baseline/final/delta flashlogs, tagged log and cleanup proof. The inherited
account-wide attribution wording is left raw; unique-tag selection is a separate
scope and is not OS per-write PID attestation. Original r14 builder and tape are
unchanged; the local driver only updates the build guard from r12 to r14.
Five diff layers, compiler logs and parent receipts are retained. The audited
original→copy set remains six DoActions (five main, one yihu), all other payloads/
header/topology and73 assets unchanged. No historical evidence or shared gate edits.

```sh
python3.11 evidence/oracle/native-fight-r15/analyze.py
python3.11 evidence/oracle/native-fight-r15/analyze.py --require-oracle
python3.11 -m unittest discover -s evidence/oracle/native-fight-r15 -v
```

Copy-byte audits need the receipt-pinned temporary movie copy; missing copies fail
closed. analysis-gates.json and checks.json record actual exits and checks.

Further work is needed to explain the missing post-goto and validate a complete
true branch without inventing continuation/lifetime semantics. Independent
per-edge OS issuance/dispatch evidence and calibrated cross-clock correspondence
with measured bounds remain absent; System Events command brackets cannot supply
them. Certified scheduling, full RNG/exclusive trace, deterministic repeat and
observer noninterference also remain unproved. Any next live needs concrete
preparation; this package performs only the single authorized run.
