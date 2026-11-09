# M0-02 r17: lexical post-goto continuation breadcrumb (offline)

Base: `a7d4c4e000a986dc098315b3350d44ee9fa48c42` (merged #259).
No Flash launch or live capture. All five flags remain false:
production_admitted, native_parity_proven, oracle_accepted,
certified_global_tick, os_input_join_proven. M0-02 remains pending.
Official remaining UNKNOWN; not claiming above the floor.

## Prepared source change

Locked source: `scripts/fighter/yihu.json`,
`DefineSprite_16/frame_1/DoAction.as`, both `doStand()` and
`doAllAction(special)`. Both existing no-argument `nornalhit()` true branches are
covered; r15 observed only doAllAction, which does not establish doStand is
unreachable. The inherited 39 lexical key forwards and decision-installed
marker remain. There is no global API hijack or native goto wrapper.

After the existing consumer-goto-before and before the original goto, save:

- a local reference to the existing `_root.__m002Emit` function;
- one primitive string containing the literal unique build run tag, escaped
  helper path, helper-local serial and literal source site.

Emit `continuation-prep` using that reference and string. Execute the unchanged
`_parent.gotoAndPlay("砍1")` once. Immediately attempt
`__m002ContinuationSink("continuation-breadcrumb", __m002ContinuationData)`.
Only then execute the unchanged dynamic consumer-goto-after statement.

The breadcrumb statement makes no fresh helper/body/root reads and performs no
post-goto attribution serialization. The retained sink itself still reads the
original root logger state, sequence, timer and phase. This is not an independent
native logging channel, and local variable/sink availability after goto is not
proved. Saved attribution describes pre-call source context, not surviving
helper identity. Both markers can be absent without establishing the cause.

Original predicate evaluation, short-circuit expressions, goto receiver/argument
and goto call count are unchanged. Added observation work may affect timing;
noninterference is unproved. No forced timeline or manufactured input/result.

## Offline compiler and tag audit

The builder layers r14 on a fresh temporary copy, then imports only the modified
yihu DoAction. Offline build: `/tmp/bvn-m002-r17-offline-01`, tag
`m002-r17-offline-20261110`. This tag is for compilation only; future live must
rebuild with a fresh unique tag. No SWF is committed.

Relative to r14: only `root/19:39/sprite16/1:12` changes in yihu.
Relative to locked originals: the inherited **six DoAction** scope is retained:
main boot, root frame8, Sprite1813 timer, Sprite1900 loader, Sprite1991 camera;
yihu Sprite16. All 75 output asset hashes are rechecked. Build receipts, compiler
stdout/stderr and source diff are retained here; parent receipt hashes are pinned
by child receipts. `build.json` pins the builder and modified copy hashes.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r17/build_observer.py \
  --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-m002-r17-new-copy --run-id UNIQUE_NEW_TAG
```

FFDec is inherited receipt-pinned; its local path may be replaced with the same
verified jar. Output must be fresh and temporary, never locked assets.

## Pairing and refusal

`classify(rows, run_tag)` is an additive observation classifier, not an admission
gate. Future capture must first establish fresh exclusive tag, contiguous raw
rows, original/copy/player hashes, PID/input/focus and cleanup provenance; a
caller must use the inherited strict raw parser before this classifier.

A matched diagnostic requires a contiguous exact query → four actual non-AI
short-circuit key returns → true full predicate → goto-before → prep → breadcrumb.
It requires same helper/site/serial/body, unique observed installation and query
identity, matching run tag, and no interleaved or duplicate breadcrumb. It reports
whether the separate dynamic after channel is observed; it never manufactures
that channel. A breadcrumb match does not replace r15's stricter consumer join
or the unchanged full-prefix r05 structural gate.

Classifications: `matched`, `prep-without-breadcrumb`,
`breadcrumb-without-prep`, `interleaved-ambiguous`. Unclaimed breadcrumbs remain
explicit orphan diagnostics. Missing, duplicate, foreign, AI, incomplete-key or
interleaved evidence never becomes matched. All classifications leave admission,
global tick and OS input join false.

Both CLI modes replay immutable r15, which contains **zero** new prep/breadcrumb
markers. They retain r16's true candidate with cause unproved, keep all raw rows,
and exit1 with `Incomplete actor state at clock boundary`. They do not write
historical reports. Synthetic test matches are parser tests, not native evidence.

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r17/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r17/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r17 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

## Next authorized live: required after this Draft

Use the retained exact movie-PID AX/CG/System Events physical menu path, fresh tag,
main+yihu pins, full trace and cleanup receipts. No live performed here.

1. Does a non-AI true predicate produce matching prep and immediate breadcrumb?
   All-false predicates cannot validate this path.
2. If breadcrumb appears but dynamic after does not, source continuation and
   emission through the saved sink were observed, but the old dynamic after
   channel was not. The precise failed dependency remains unknown.
3. If prep appears without breadcrumb, no cause is proved: continuation, locals,
   sink execution and log delivery remain unresolved. No inferred abort/removal.
4. If both appear, only these source observations are established. Native dispatcher
   return, helper lifetime and later-frame action execution remain unproved.

Full initial state/tick certification, calibrated per-edge OS input join, full
RNG/trace, deterministic repeat and original/copy noninterference remain separate
requirements. No readiness transition, merge, deployment or production closure.
