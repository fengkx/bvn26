# r13: live startFight/menu marker validation

One authorized run from master c75da4e5 (#255), **99.272 seconds**, movie PID
**43607**, tag **m002-r13-live-20261109-b81d**. Physical menu→Vs Com→一护/Naruto
fight tape completed, including0.5s physical J. No second run. No human-only
prompt, TCC error or focus-loss failure. Pre-activation frontmost PID21273;
all17 subsequent sampled focus probes show43607. These are boundary samples,
not continuous focus monitoring. Owned cleanup left no movie PID. Original and
all75 copy hashes, including main+yihu, passed final recheck.

production_admitted=false, native_parity_proven=false, oracle_accepted=false.
M0-02 pending. Official remaining UNKNOWN; not claiming above floor.

## Actual source-boundary facts

The unique startFight interval passed the **unchanged r12 shape checker**:

| seq | Event | Actual decoded fields |
|---:|---|---|
|3201|startfight-entry|zhanting=true, readying=false, menuEnabled=false, gamePaused=false, p2loaded=true, rootframe56|
|3204|startfight-state-written|zhanting=false, readying=false, menuEnabled=false, gamePaused=false, p2loaded=true, rootframe56|
|3205|menu-write-before|requested=true, menuEnabled=false, visible=false|
|3206|menu-write-after|requested=true, menuEnabled=true, visible=false|
|3207|menu-exit|requested=true, menuEnabled=true, visible=false|
|3208|startfight-exit|zhanting=false, readying=false, menuEnabled=true, gamePaused=false, p2loaded=true, rootframe56|

Entry getTimer84115; subsequent interval markers getTimer84117; all carry camera
ordinal468/between-game-callbacks. Actor snapshots immediately after entry/exit
show both HP1000 and retained identical state fields. This observes the source
function body and state outcome, not native dispatcher/unwind or certified global
tick. **Readying was already false at entry**; do not claim a true→false change.
Menu enabling did not show the menu. Earlier, seq3/4/5 was a separate disabling
invocation: requested=false/menuEnabled=false, visible true→false by normal end.
It is retained and not folded into the startFight interval.

All7,866 tagged events are retained with contiguous sequence and fresh-tag raw
selection. Counts: one each startfight-entry/state-written/exit; two each menu
before/after/exit;2 loader requests;4 load-complete entry/exit pairs;13 decision
installations; one chushi before/after;771 camera pairs;3,192 actor-state rows;
25 timer pairs;278 intro key queries;1 music random result;1 boot/ready marker.

There are **2,767 fight-key-return events**, **one true yihu-decision-9** (nornalhit
slash query, code74, owner/game/p1/mc, non-AI/unpaused) at seq6649/getTimer90810/
local ordinal668. Physical J and this return do not certify downstream consumption
or an input→global-tick mapping. No deterministic repeat or observer noninterference
comparison was attempted.

## Retained structural refusal

HP before/after markers are seq1139/1142, getTimer74582/74583, camera ordinal182,
paused=true. Ten timer boundaries (ordinals1–5 entry/exit) retain undefined HP.
All source rows remain intact. Both analysis modes return **1**; the unchanged r05
whole-prefix structural function still refuses `Incomplete actor state at clock
boundary`. Successful source-boundary shape is separate from actor/trace admission.

`analyze.py` verifies session/build equality, unique fresh raw/tag selection,
append-only interval, physical input PID returns, cleanup, all retained copy hashes
and the exact changed-tag set. It reports all startFight/menu fields, identifies
source entry→normal-end intervals, rejects missing/nested/unmatched/reordered or
interleaved marker sequences and runs unchanged r12 shape checks per interval.
Outside menu calls are retained separately; they are not attributed by proximity.
Shape validation is not a complete actor/instance/clock or production oracle gate.

Raw session, window probes, input operations, nine screenshots, pre/baseline/final/
delta logs and cleanup receipts are under run-01. Account-wide attribution text in
the inherited session is preserved raw; fresh-tag selection is separate and is not
OS per-write PID attestation. Missing temporary copies fail closed in the byte-audit
recheck; repository-only raw receipts remain available.

## Build and recheck

Unmodified r12 builder produced a fresh temporary copy. All four diff layers,
compiler logs and parent build receipts are retained. Six original→copy DoActions
remain the audited set (five main, one yihu), all other payload/header/topology
and73 other assets unchanged. Capture driver only changes r09's facility guard
from r08 to r12; main+yihu hash checks and physical tape remain unchanged. No locked
assets, historical receipts, runtime, contracts or shared validators were edited.

```sh
python3.11 evidence/oracle/native-fight-r13/analyze.py
python3.11 evidence/oracle/native-fight-r13/analyze.py --require-oracle
python3.11 -m unittest discover -s evidence/oracle/native-fight-r13 -v
```

See analysis-gates.json and checks.json for actual exits, tests and project checks.
Both modes intentionally exit1 regardless of source-shape success. Tests cover
raw-log/build tampering, retained HP refusal, exact PID/focus binding, outside-menu
separation, missing/nested/ambiguous intervals and false menu outcomes.

## Remaining work / further live

This run validates marker firing, source-body order and recorded state outcomes.
It does not establish certified scheduling/global ticks, downstream input consumption,
complete random tape/provenance, full exclusive contract trace, stable loaded instance
identity, deterministic repeat or same-input original/instrumented noninterference.
Source end markers are not native dispatcher return proof. The body marker interval
cannot silently become a global initial-state tick or erase the loading prefix.
Further live evidence is required for those obligations, after concrete preparation;
no extra live run was performed here. M0-02 is not closed.
