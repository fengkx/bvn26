# M0-02 r20: live direct Trace before without after

Base `8ba2972cd96391bfdfae59796be3ea9c1a00a695` (merged #262).
One authorized live run, no second run. All five flags remain false:
production_admitted, native_parity_proven, oracle_accepted,
certified_global_tick, os_input_join_proven. M0-02 pending.
Official Codex remaining UNKNOWN; not claiming above the floor.

## Capture and provenance

Run-01: tag `m002-r20-live-20261110-d48b`, movie PID28648, receipt duration
**85.3545937538147 seconds**, including launch/tape/capture/cleanup. The retained
physical tape follows Normal → Vs Com → 一护/Naruto → Kon/Gaara → present-world
→ fight, including physical J held0.5s. Screenshots show the fight, not certified
consumption or downstream action execution.

Exact movie-PID AX/CG ownership and System Events input; no CUA app-string bind.
Capture lock acquired. Initial frontmost PID21273 before activation; all17 later
input-boundary focus probes show owned PID28648 with exact movie window. This is
sampled evidence, not continuous foreground monitoring. No observed TCC/focus/
human-only blocker. Cleanup targeted only PID28648; remaining movie PIDs `[]`.

Player SHA256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`;
OS/Rosetta/trace configuration, input and binding tool pins in session.json.
Locked assets and all75 copied assets rechecked before/after. Fresh r19 build in
`/tmp/bvn-m002-r20-live-01`; actual owned movie copy path is in the receipt. Main+
yihu build identity is tied to session and hashes. Original→copy remains six
DoAction changes. No original assets, runtime, shared gates or r01–r19 evidence
changed. No forced timeline, AS input or substituted key/random results.

## Both channels in original order

`combined.log` is byte-identical to `flashlog.after.log`, including unknown output
and warnings, not a filtered union of tags. `tagged.log` is the legacy root-only
selection. Prelaunch and input-baseline files plus actual append delta are kept.
The driver checks freshness of root `M002|tag|` **and** side `M002SIDE|tag,` before
launch. Analysis rejects foreign root/side tags, reordered combined bytes,
noncontiguous root sequence, build/source/copy/player/tool/tape mismatch, missing
physical input/focus/cleanup receipts. Unknown raw lines remain ordering barriers
in the r19 combined parser; none are discarded to obtain a match.

There are **7,543 root events** and **one side event**. Other raw lines remain
unclassified barriers, not certified game events. Root-tag exclusivity is not a
proof of full native trace completeness. The inherited session's generic account-
wide attribution describes raw flashlog capture, not oracle admission.

## Actual true candidate and refusal

`/game/p1/mc/instance3402`, local serial23, doAllAction:

| Root sequence / combined raw line | Observation |
|---|---|
| seq6451 | non-AI query-before |
| seq6452–6455 | sites9/10/11/12: true/false/false/false |
| seq6456 | full predicate=true |
| seq6457 | consumer-goto-before |
| seq6458 / line6581 | matching continuation-prep |
| line6582 | matching M002SIDE direct **before** |
| seq6459 / line6583 | next camera game-state; not a side after |
| seq6465 | another helper installation, not removal proof |

Whole capture counts:

- side-before **1**, side-after **0**;
- continuation-prep **1**, sink continuation-breadcrumb **0**;
- dynamic consumer-goto-after **0**.

The unchanged r19 classifier reports **before-without-after**, cause **unproved**,
source_continuation_observed=false. The unchanged r17 classifier reports
prep-without-breadcrumb. No matched direct interval exists. The before observation
is reached through a direct Trace rather than root sink, but it does not prove
execution of the post-goto Trace or explain its silence. Local register lifetime,
execution continuation and native Trace delivery remain unresolved. Later camera
logging rules out mere end-of-capture at before, not a particular failure cause.
No claim of goto nonreturn, helper removal, abort or logger failure is made.

197 consumer candidates:196 false-predicate doAllAction intervals validate under
unchanged r15 rules, one true candidate remains unjoined. No doStand interval
observed. 2,187 fight-key queries,2 positive (yihu-decision-9), not certified OS
consumption ticks. Inherited startFight/menu seq3305–3312 passes r12 shape.
**10 early incomplete HP clock boundaries** remain. Both analysis modes exit1:
`Incomplete actor state at clock boundary`.

## Checks and limits

12 r20 receipt/binding tests include combined-order/foreign-side tampering and
actual before-without-after regression. Eight unchanged r19 tests exercise
synthetic pairing/refusals and retained bytecode. Those synthetic matches are
not r20 native evidence. verify/handoff/diff checks pass; checks.json retains
actual exits. All observations, failed intervals and raw incomplete boundaries
are retained. No admission rule is relaxed to admit side-before.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r20/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r20/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r20 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r19 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

Live analyzer rechecks receipt-pinned temporary copies and player; their absence
fails closed. Build tool paths are receipt-pinned local examples, not bundled
binaries. No further launch is part of a recheck.

Further work is required before another discriminating live: root-logger-only
failure is not an established explanation, and direct after remains unobserved.
Investigate exact native continuation/lifetime/Trace obligations without assuming
a cause or simply repeating this tape. Future independent observations would be
needed to resolve those gaps. No second capture was run here.

Even a future side-after match would not prove native dispatcher return, helper
lifetime, later-frame action, global tick, calibrated per-edge OS input join,
complete initial state/RNG/trace, deterministic repeat or observer noninterference.
M0-02 stays pending. No ready transition, merge, deployment or promotion.
