# M0-02 r21: local-free literal Trace preparation (offline)

Base `fe2a0baf3298c332ead1473e136b048b3f5f8e9b` (merged #263).
No Flash launch or live capture. All five flags remain false:
production_admitted, native_parity_proven, oracle_accepted,
certified_global_tick, os_input_join_proven. M0-02 pending.
Official remaining UNKNOWN; not claiming above the floor.

## Comparison: observations, not a causal experiment

| Run | Candidate | Observed before goto | Observed after goto |
|---|---|---|---|
| r18 | instance3315 / serial213; seq8210–8217 | full true predicate, goto-before, saved-sink prep | no breadcrumb or dynamic after; no direct channel installed |
| r20 | instance3402 / serial23; seq6451–6458, combined line6582 | full true predicate, goto-before, prep, direct Trace-before | no direct after, breadcrumb or dynamic after |

r18 remains prep-without-breadcrumb; r20 remains before-without-after.
Cause remains **unproved**. Later camera logs and other helper installation paths
are retained, not converted into continuation or removal evidence. These runs
have different tags, helper instances, timing and uncontrolled random state;
they are not a same-input deterministic/noninterference comparison. R18 did not
have a direct channel, so its absence there is not a failed direct Trace.

`historical-pins.json` pins both runs' actual raw logs/build/session receipts.
`diagnosis.json` replays full raw order and retains exact candidate neighborhoods,
original sink/direct classifications and structural refusals. No history is
rewritten, no incomplete state is trimmed or filled.

## Exact source and bytecode

Locked source `scripts/fighter/yihu.json`,
`DefineSprite_16/frame_1/DoAction.as`, reconstructed through r07/r14/r17/r19 with
the r20 tag. Reconstruction equals the retained r20 compiler input byte-for-byte.
The r20 yihu temporary copy was hash-matched against its committed build receipt
before P-code export. Source/P-code exports, jar/SWF hashes, commands and logs are
retained in this package (`bytecode-receipt.json`).

The existing true branch order at both doStand/doAllAction is:
prep → construct local before/after strings → Trace(local before) → original
`_parent.gotoAndPlay("砍1")` → Trace(local after) → saved-sink breadcrumb →
dynamic after. P-code shows original goto CallMethod/Pop followed by
`Push register<after>; Trace`. It does not contain an explicit Return/Jump between
that call and this Trace. This proves encoded layout, not actual native progress.

Dependency distinctions:

- Direct side-after reads a saved local/register string, then executes Trace.
  It avoids root logger calls but does not prove register availability after goto.
- Saved-sink breadcrumb also needs saved function/data registers; its function
  checks root Ended and reads/increments root sequence, timer, ordinal and phase.
- Dynamic after additionally resolves helper/body/root fields and serializes them.
- All channels require the corresponding instructions to execute and output to
  reach the log. No trace receipt establishes why a later instruction is silent.

No offline artifact proves helper removal, AVM abort, nonreturn, register loss,
or Trace delivery failure. Path changes/installation markers are not lifetime
proof. We make no external AVM lifecycle claim; instruction names/layout come
from pinned P-code, not an assumed runtime model.

## Minimal next facility

The new builder layers r19 and adds **literal** before/after Trace statements
around the same original goto at both true-branch sites. Existing direct-local,
saved-sink and dynamic channels remain unchanged. The literal payload is compiled
from fresh run tag + literal source site + phase:

```actionscript
trace("M002LITERAL|UNIQUE_TAG|doAllAction|before");
_parent.gotoAndPlay("砍1");
trace("M002LITERAL|UNIQUE_TAG|doAllAction|after");
trace(__m002DirectAfter);
```

The equivalent doStand site has its own literal site. P-code tests prove the new
post-call prefix is `Push "M002LITERAL|...|after"; Trace`, not a register/property
read or a logger call. No post-goto local variable is needed for this statement.
It still requires the action context/constant operand and Trace execution/delivery;
absence is still inconclusive. No try/catch, wrapper, extra goto, forced timeline,
API hijack, manufactured input/result or native return claim. Original predicate,
short-circuit expressions and goto receiver/argument/count are unchanged.
Observation timing/noninterference remains unproved.

Offline output `/tmp/bvn-m002-r21-offline-01`, tag
`m002-r21-offline-20261110` (not live). Original→copy retains six DoAction tags;
relative to r19 only yihu Sprite16 DoAction changes. All75 copied asset hashes
rechecked. Build/source-diff/P-code/compiler/tag receipts retained; no SWF committed.
FFDec host log-file permission warnings remain in stderr; compile/export exited0
and audits passed. No permission widening or Flash launch for compilation.

## Literal pairing remains fail-closed

The literal payload intentionally has **no helper/serial identity**. It cannot
identify an invocation by itself. The classifier requires the original combined
raw order with adjacent root-prep → matching direct-side-before → literal-before
→ literal-after, plus the inherited r17 full contiguous non-AI true-predicate
prefix and unique observed helper/query identity. Unknown log content remains a
barrier. Missing, orphan, mismatched-site/tag, duplicate or interleaved evidence
is refused; timestamps and local serial proximity are never a substitute.

Even `matched-literal-source` means an observed marker sequence, not a certified
native lifetime/dispatcher return. It never fills missing old-channel events or
changes r15/r17/r19 admission. The literal channel's weaker payload identity is
why isolated literal-after is explicitly unjoined.

Future capture must retain **all three prefixes** (`M002`, `M002SIDE`,
`M002LITERAL`) in byte-original combined order, verify freshness/foreign tags,
main+yihu/player pins, exact movie PID input/window/focus and owned cleanup. This
slice prepares a parser/classifier, not a new capture driver. Both CLI modes only
replay r18+r20: zero literal events and unchanged `Incomplete actor state at clock
boundary` refusals; exit1. Synthetic test insertions are tests, never evidence.

## Next authorized live is required

Historical logs cannot answer whether a literal post-goto Trace executes/delivers.
After this Draft, adapt the physical PID capture for all prefixes and a fresh tag:

- Literal-after observed but local side-after absent: continuation/output through
  the literal statement observed; the exact local-channel failure remains unproved.
- Literal-before but no literal-after: still cannot distinguish absent continuation
  from action-context/Trace delivery failure. Do not infer helper removal or abort.
- All after channels observed: only source observations, not native dispatcher
  return, helper lifetime, later-frame action or original/copy noninterference.
- Missing unique prefix or interleaved marker: reject attribution.

Further live is needed after this preparation; no live performed here. Global
tick, calibrated per-edge OS join, full initial state/RNG/trace, deterministic
repeat and noninterference remain independently unproved. No readiness, merge,
deployment or production promotion.

## Recheck

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r21/build_observer.py --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar --output /tmp/bvn-r21-new-copy --run-id UNIQUE_NEW_TAG
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r21/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r21/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r21 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

CLI analysis modes exit1. Seven tests cover pairing failures, comparative replay,
source patch reversal/original call counts, and literal P-code at both sites.
Replay/tests use repository receipts, not temporary copies. Build/export tool
paths are examples backed by jar hashes; output must be fresh and temporary.
