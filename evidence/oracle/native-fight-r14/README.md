# r14: source consumption preparation, not a certified tick

Offline only on master5e35f58e8de9a551d0418857a2c12369daab00cc (#256).
No Flash launch/capture/input. Official remaining UNKNOWN; not claiming above floor.
production_admitted=false, native_parity_proven=false, oracle_accepted=false;
M0-02 pending. certified_global_tick=false and os_input_join_proven=false.

## Missing join, established from actual r13 receipts

`analysis.json` pins r13's build/session/raw tagged log and retains the physical
fight-J operation plus its one positive query. Python records command-start wall
and monotonic time and command-return monotonic time. The AppleScript performs
focus delay, key-down, hold and key-up before returning. These are **command
brackets**, not per-edge dispatch acknowledgement or native consumption timestamps.
Flash records getTimer and a camera-local ordinal in another clock domain. There
is no observed/calibrated mapping or uniquely acknowledged input event joining
the two. No offset is fitted from a nearby positive return or startFight marker.

The positive yihu-decision-9 observes only `_parent.kis(_parent.斩)` inside
`scripts/fighter/yihu.json:DefineSprite_16/frame_1/DoAction.as`, function
`nornalhit(combo)`. Its non-AI predicate also requires NOT jump, up and down.
A true first query alone does not prove the full predicate, caller or action.
The two exact no-argument consumers are `doStand()` and `doAllAction(special)`;
each has `if(nornalhit()) { _parent.gotoAndPlay("砍1"); }`.

The source callback at
`DefineSprite_638/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`
calls doAllAction after gameRunning. This identifies one source caller; it does
not make all helper invocations one global frame or prove that callback ran for
the r13 positive. The old query trace lacks this consumer interval. doStand is
instrumented as the other exact predicate consumer, without inventing its caller.

## Narrow additive observer

The r12 temporary copy is retained, including39 lexical key sites and existing
loader/chushi/startFight/timer markers. This extension changes only main boot
DoAction and yihu Sprite16 DoAction relative to r12:

- Before each of the two original predicates: increment a **helper-local** serial
  and emit consumer-query-before with helper target, serial, source site, body
  target/frame and actual useAI.
- Evaluate original `nornalhit()` exactly once in its original caller expression;
  pass that actual result to a root observer which logs it and returns unchanged.
  The original short-circuit key expression itself is untouched.
- Only inside the **original true branch**, log consumer-goto-before, execute the
  original gotoAndPlay once, and log consumer-goto-after with actual target/frame
  and useAI. False predicates execute no goto and no goto markers.

The serial is instrumentation state, **not a frame or global tick**. It resets on
helper script execution; paths/serials are not proven lifetime identities. Reused
paths, reinstallation and reentrancy require future interval/instance evidence.
The post-goto marker is source continuation, not native dispatcher return or
proof of downstream action execution on a later frame. Nothing forces a timeline,
substitutes input, replaces native APIs or changes the original branch result.
Observation overhead and argument/property reads still require noninterference
validation. No gameplay output is accepted from compilation or source restoration.

SOURCE_FIRST: unique exact consumer blocks are bound to named functions, and any
inventory drift fails closed. Removing inserted code restores the inherited
fighter source exactly in tests; original predicate/goto call counts are unchanged.
No placement/MOVE/lifecycle tag changes occur. No source mechanism is implemented
or declared complete; runtime and historical evidence stay untouched.

Final independent-copy scope remains six original→copy DoActions (five main,
one yihu). All other tag payloads/header/topology and73 other assets unchanged.
The first offline build was refined to include useAI; retained final receipt is
`/tmp/bvn-m002-r14-offline-02`, not a claim of repeat/noninterference.
Parent build receipts, five diff layers and compiler logs are retained; inherited
hash fields identify their parent builders, consumer_* fields identify r14.

```sh
python3.11 evidence/oracle/native-fight-r14/build_observer.py \
  --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-m002-r14-recheck \
  --run-id m002-r14-offline-recheck
python3.11 -m unittest discover -s evidence/oracle/native-fight-r14 -v
python3.11 evidence/oracle/native-fight-r14/analyze.py
python3.11 evidence/oracle/native-fight-r14/analyze.py --require-oracle
```

Both CLI modes return1. Immutable r13 has zero consumer markers; its whole prefix
still fails unchanged r05 validate_rows with Incomplete actor state at clock
boundary. No loading row is filled/removed. Shape-only tests reject wrong owner/
serial/site, missing exit, false-predicate goto and AI/unknown branches. Even a
synthetic valid source interval has os_input_join_proven=false and
certified_global_tick=false. It is not an acceptance adapter or OS join validator.

## What later live must establish (none executed here)

1. Under a new tag and receipt-matched main+yihu movie, retain the full raw prefix,
   physical input receipts, helper-install events and the new consumer intervals.
   Join key-return events only within a unique, nonambiguous helper invocation;
   require non-AI branch and observed full predicate before attributing the source
   goto. Reject missing/interleaved/reinstalled ambiguous intervals. Serial or
   timestamp proximity alone is insufficient.
2. Separately obtain legitimate per-edge input issuance/dispatch evidence and an
   independently validated cross-clock/event correspondence with measured bounds.
   The current System Events command bracket cannot supply that. This slice does
   not implement such synchronization and makes no promise that an extra trace
   marker alone can certify it. No AS-as-input or manufactured synchronization.
3. Establish ExecutionProfile scheduling/phase semantics including actor callbacks,
   timer callbacks, pauses, placement/lifetime and downstream action execution.
   Camera ordinals, timer ordinals and the new helper serial remain separate local
   domains; none is relabeled a universal tick.

Existing artifacts cannot certify that join retrospectively. A future live run
is needed to validate these source consumption markers, and further facility work
is needed before claiming certified input/global ticks. The exact missing signals
are listed above; no live was needed to place this narrow source observer.
Complete RNG tape/provenance, full exclusive trace, deterministic repeat and
same-input original/instrumented noninterference also remain unproved.
