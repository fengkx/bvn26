# M0-02 r16: missing post-goto observation bounds (offline)

Base: `07e215765eef441c92b24073c4a06c398ae02cea` (merged #258).
No Flash launch, new SWF, runtime fix, or native observation in this slice.
All five flags remain false: production_admitted, native_parity_proven,
oracle_accepted, certified_global_tick, os_input_join_proven. M0-02 is pending.
Official Codex remaining UNKNOWN; not claiming above the budget floor.

## What the receipts establish

The immutable r15 trace has 7,992 contiguous events. Its 224 doAllAction
candidates still yield 223 validated false-predicate source intervals and one
refused true candidate. No doStand interval or consumer-goto-after is observed.

For `/game/p1/mc/instance2901`, local serial142:

- seq6973: query-before, non-AI, body `/game/p1/mc`.
- seq6974–6977: sites9/10/11/12 return true/false/false/false.
- seq6978: full predicate result true.
- seq6979: goto-before. This is not evidence that the following native call
  completed, nor even an independent native call-entry receipt.
- seq6980: camera game-state logging resumes; seq6986 records installation at
  `/game/p1/mc/instance3012`. Neither establishes removal of instance2901.
- No post-goto marker exists anywhere in the trace. Subsequent unrelated keys,
  reinstalls and interleaving remain rejected by the unchanged r15 joiner.

`diagnosis.json` preserves the seven-event prefix, next events, later installation
receipts, original refusal and counts. It does not splice a later key or event
into the refused invocation. Later logging excludes a simple end-of-capture at
6979; it does not prove logger availability at the missing call site.

## Exact source boundary and causal limit

`source-reconstruction.json` reconstructs both r14 replacements from locked
`scripts/fighter/yihu.json`, `DefineSprite_16/frame_1/DoAction.as`, using the retained
r07/r14 builders. Tests also match post-goto statements against r15's retained
`consumer.diff.gz`. The original branch in doStand/doAllAction is:

```actionscript
if(nornalhit()) {
    _parent.gotoAndPlay("砍1");
}
```

The observer evaluates nornalhit once, forwards its actual result, emits
consumer-goto-before, performs the original goto once, then evaluates:

```actionscript
_root.__m002Emit("consumer-goto-after",
    escape(this._target) + "," + __m002Call + ",doAllAction," +
    escape(_parent._target) + "," +
    _root.__m002Value(_parent._currentframe) + "," +
    escape(_parent._parent.useAI));
```

The doStand replacement differs only in site attribution. A successful after
record would observe **source continuation plus successful dynamic field reads,
serialization and emission**. It is not native dispatcher return, helper lifetime,
or execution of a later action frame. Its absence cannot distinguish absent
continuation from failure of any observation dependency. Helper removal, Flash
abort, logger failure and scope changes remain hypotheses, not conclusions.

The additive classifier therefore names the condition
`goto-before-observed-post-goto-unobserved`, with `cause=unproved` and the inherited
`key_join_status=not-joined`. It never repairs the missing event. A malformed or
wrong-helper after marker remains refused by the existing joiner rather than
being treated as closure. The r05 structural gate still sees the entire original
prefix and refuses `Incomplete actor state at clock boundary` (12 early boundaries).

## Minimum next discrimination, not an implemented fix

A future observer preparation should separate two observations currently fused:

1. In the same lexical true branch, before the unchanged goto, prepare immutable
   primitive attribution (run tag, source site, helper path and local serial) and
   an observation sink reference. Record that preparation before goto.
2. Immediately after the original goto, attempt a minimal continuation breadcrumb
   using only the prepared attribution, **before any fresh helper/body field
   reads**. Keep the original dynamic after marker as a separate diagnostic.
3. Require an unambiguous matching prefix and breadcrumb; a breadcrumb without
   the dynamic marker would distinguish reached continuation from successful
   dynamic observation. Absence of both remains inconclusive, including local
   variable/sink availability. Do not turn absence into helper-removal proof.

This is a capture specification, not compiled or live-validated AS. Choosing and
validating a retained sink across scope/lifetime changes needs a separate narrow
observer build and original/copy tag audit before launch; adding a root wrapper
around the native goto now would change call context without establishing the
cause. We deliberately do not make that speculative correction. Any prepared
marker must leave receiver, argument, predicate and goto call counts unchanged,
retain all rejected rows and preserve fail-closed joins. No forced frames, API
hijack, synthetic return or injected input is permitted.

Live is needed **after** that preparation: historical receipts contain no
independent continuation breadcrumb. A future authorized positive predicate must
exercise the exact source branch; an all-false run cannot validate this gap.
Record complete tagged prefix, main+yihu identity, exact movie PID input/focus,
cleanup and audit receipts. Even a successful breadcrumb would not certify
native dispatcher return, downstream action execution, global tick, OS input
join, full RNG/trace, deterministic repeat or observer noninterference.

## Recheck

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r16/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r16/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r16 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

Both analysis modes exit1. Targeted tests include EOF silence, continued logging,
wrong-helper after refusal, exact reconstruction and immutable replay. Input pins
are repo-relative; replay does not require surviving /tmp copies and does not
re-certify original capture provenance. No historical analyzer with report-writing
side effects is called. No compiler/tag audit is newly claimed: there is no new
SWF or observer in r16. Existing six-DoAction build receipts remain immutable.
