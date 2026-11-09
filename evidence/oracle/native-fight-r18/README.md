# M0-02 r18: live continuation-prep without breadcrumb

Base: `4db9fe43fb4f05f16b9ec43e5ee615bdc37cd35f` (merged #260).
One authorized live run; no second run. All five flags remain false:
production_admitted, native_parity_proven, oracle_accepted,
certified_global_tick, os_input_join_proven. M0-02 remains pending.
Official Codex remaining UNKNOWN; not claiming above the floor.

## Actual run

- Round: run-01; tag `m002-r18-live-20261110-a83d`.
- Movie PID15906; receipt duration **92.17166590690613 seconds**, including launch,
  physical tape, capture and cleanup. Player/session/OS/Rosetta/trace configuration
  and tool pins are in `run-01/session.json`.
- Retained r15 physical menu tape, exact movie-PID AX/CG/System Events binding,
  Normal → Vs Com → 一护/Naruto → Kon/Gaara → present-world → fight, including a
  0.5-second physical J. No CUA Flash app-string binding, forced frames or AS input.
- Lock acquired; only owned PID15906 cleaned up; remaining movie PIDs `[]`.
  Original assets and all 75 copied assets passed before/after hash checks.
- Before activation, frontmost PID21273. All **17 post-activation before/after
  input probes** recorded PID15906 frontmost with the exact AX/CG movie window.
  This is sampled focus evidence, not continuous foreground surveillance.
- No observed focus/TCC/human-only blocker. `08-fight-j.jpg` visibly shows the
  fight; screenshots do not certify internal input consumption or action execution.

The build was made offline by r17 in `/tmp/bvn-m002-r18-live-01`, then copied to
an owned unique temporary movie directory recorded in the session. Player SHA256:
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
Main and yihu source/copy hashes, full output hashes, parent build receipts and
compiler/source-diff receipts are retained. Original→copy scope remains six
DoAction tags. No locked game/script or historical evidence was changed.

## Observed continuation facts

10,420 contiguous exclusive-tag events; 4,082 fight-key queries, **2 positive**
(both yihu-decision-9). These are observed query returns, not OS consumption ticks.
341 doAllAction consumer candidates: 340 false-predicate source intervals validate
under the unchanged r15 joiner; one true candidate is refused. No doStand interval
was observed.

True candidate: `/game/p1/mc/instance3315`, helper-local serial213, doAllAction:

| Sequence | Observation |
|---|---|
| 8210 | query-before, non-AI body `/game/p1/mc` |
| 8211–8214 | sites9/10/11/12 return true/false/false/false |
| 8215 | full predicate result=true |
| 8216 | consumer-goto-before |
| 8217 | continuation-prep with matching run tag/helper/serial/site |
| 8218 | next camera game-state event; not a continuation breadcrumb |
| 8224 | decision-installed at another path, instance3461; not removal proof |

Across the entire capture:

- continuation-prep: **1**
- continuation-breadcrumb: **0**
- dynamic consumer-goto-after: **0**
- r17 pairing: **prep-without-breadcrumb**, cause **unproved**;
  source_continuation_observed=false, no matched interval.

Prep establishes that saved attribution was emitted through the captured sink
before the original goto. It does not establish native call entry/return or
post-goto local/sink availability. Continued camera logging rules out simple
capture termination at prep, but does not establish that the missing breadcrumb
was attempted or why it was absent. No inference of helper removal, Flash abort,
logger failure or failed scope resolution is made. Later events are not spliced
into the refused invocation. The r15 joiner also retains the new prep event as an
interleaving error; its strict historical acceptance conditions are unchanged.

Inherited startFight/menu interval seq3085–3092 passes the unchanged r12 shape
check. **10 early HP-incomplete clock boundaries** remain in the whole trace.
Both CLI modes exit1: `Incomplete actor state at clock boundary`.
Marker observations do not override that structural refusal.

## Provenance and checks

The r18 analyzer requires fresh exclusive tag/append selection, contiguous raw
sequence, matching build/session, original and copied asset hashes/tag audit,
player/tape/binding-tool/trace pins, exact movie-PID input returns and AX/CG focus
snapshots, complete physical tape, and owned cleanup. Missing surviving temporary
copies fail closed; analysis does not silently replace them with claimed hashes.
The account-wide flashlog files are raw capture receipts. Exclusive tag selection
is separately checked; the inherited session's generic account-wide attribution
text is not itself exclusive-trace proof or a normalized fight oracle.

`observations.json` retains all rejected boundaries, consumer intervals, decoded
inherited markers and continuation classification. `checks.json` records actual
exit codes. Tests cover receipt tampering, build/PID/cleanup mismatch, window
binding rejection and the actual prep-without-breadcrumb refusal. The unchanged
r17 tests separately exercise synthetic matched/missing/orphan/interleaved cases;
those fixtures are not native observations.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r18/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r18/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r18 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r17 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

## Remaining work

The new live run proves the prep path fires on an actual non-AI true predicate;
it **does not close the post-goto gap**. Before another live, source/bytecode-level
continuation and observation-sink/lifetime investigation is needed to choose an
independent next discriminating observation. Repeating this tape alone cannot
establish the cause. Future live or native facility evidence is still required
for any new continuation claim; no second run was attempted here.

Native dispatcher return, helper lifetime, later-frame action execution,
certified global scheduling, calibrated per-edge OS input join, complete initial
state/RNG/trace, deterministic repeat and original/copy noninterference remain
unproved. Physical J, timestamps, local serials, screenshots and source normal-end
markers are not substitutes. No admission, ready transition, merge or deployment.
