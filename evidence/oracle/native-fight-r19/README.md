# M0-02 r19: source/bytecode and direct Trace preparation (offline)

Base `db6830d79865e8e760f2db975dc5494d1985473b` (merged #261).
No Flash launch/capture. Five flags remain false: production_admitted,
native_parity_proven, oracle_accepted, certified_global_tick, os_input_join_proven.
M0-02 pending. Official remaining UNKNOWN; not claiming above the floor.

## Retained r18 evidence and causal bounds

R18 helper `/game/p1/mc/instance3315`, local serial213, doAllAction:
seq8210 query;8211–8214 actual non-AI key returns true/false/false/false;
8215 full predicate true;8216 goto-before;8217 continuation-prep.
No breadcrumb or dynamic after anywhere. Seq8218 continues camera logging;
8224 installs another helper path. These are not helper-removal or native-return
receipts. R17 classification remains prep-without-breadcrumb, cause unproved.

The historical input pins, exact candidate through seq8224, source reconstruction,
retained compiler diff and receipt-matched yihu P-code are available in this
package. R18's temporary yihu hash was verified against its committed build
receipt before export. No historical evidence or analyzer output was rewritten.

## What the source and bytecode actually establish

Source: locked `scripts/fighter/yihu.json`,
`DefineSprite_16/frame_1/DoAction.as`, reconstructed through r07/r14/r17 builders
with the r18 tag. Both doStand/doAllAction contain the original predicate and goto.
`r18-reconstructed-source.as.gz` retains the complete reconstructed source.
`r18-sprite16.pcode.gz` is FFDec's P-code export of the receipt-matched live copy.
`bytecode-receipt.json` pins input SWF, jar, commands and exported bytecode.

In the r18 doAllAction P-code:

1. GetMember of `__m002Emit` is saved via StoreRegister6.
2. Primitive tag/helper/serial/site attribution is saved via StoreRegister7.
3. Prep is emitted with register7 plus literal `continuation-prep`, register6,
   undefined and CallMethod; its result is popped.
4. `Push "砍1"`, argument count1, register3, `"gotoAndPlay"`, CallMethod, Pop.
5. Register7 and literal `continuation-breadcrumb` are passed to register6 via
   CallMethod, then Pop. Fresh helper/root-dependent dynamic-after reads follow.

Thus the compiler retained a post-goto breadcrumb call in the encoded instruction
stream. Between that goto CallMethod and breadcrumb operands there is no explicit
Return/Jump instruction. This is **static instruction layout**, not evidence of
native execution of the next instruction or dispatcher return. Tests check both
exact attack sites; doStand register numbers may differ.

The saved sink points to the inherited function in
`evidence/oracle/native-fight-r03/observer.as`. That function checks
`_root.__m002Ended`, increments `_root.__m002Seq`, reads getTimer and root ordinal/
phase, concatenates the payload, then traces. Saving a function reference does
not remove those dependencies. Its prep fire proves this channel worked before
the goto, not afterward. Registers/local availability after goto, logger execution,
root state and output delivery remain unproved at the missing boundary. No AVM
abort/removal semantics are inferred from a static CallMethod or missing trace.

No external AVM behavior claim is needed for this conclusion: sources and pinned
P-code establish only the encoded operations. Helper removal, execution abort,
goto nonreturn and sink failure remain possible questions, not diagnosed causes.

## Narrow additive facility

`build_observer.py` layers r17 and modifies only the existing two true branches.
After root continuation-prep, construct two primitive local strings:
`M002SIDE|<saved tag,helper,serial,site>|before` and `...|after`.
Execute direct `trace(before)`; execute the unchanged original goto once; execute
direct `trace(after)` **before** the unchanged saved-sink breadcrumb and dynamic
consumer-goto-after. No new root function, global override, try/catch, goto wrapper,
forced timeline or manufactured result. Predicate and short-circuit calls unchanged.

The compiled r19 P-code at both sites is:

```text
Push register<before>
Trace
Push "砍1"
Push 1
Push register<original parent>
Push "gotoAndPlay"
CallMethod
Pop
Push register<after>
Trace
Push register<saved attribution>
Push "continuation-breadcrumb"
...
```

This removes root logger calls, dynamic helper/body reads and post-goto string
construction from the new after statement. It still depends on the saved local
register and the player's Trace/log delivery. It is a separate observation path,
not an independently proven native dispatcher/lifetime sensor. Noninterference
and timing effects are unproved.

Offline build `/tmp/bvn-m002-r19-offline-01`, tag
`m002-r19-offline-20261110`; **not a live tag**. Both main+yihu output hashes and
all 75 copy hashes checked. Relative to r17 only yihu Sprite16 DoAction changes;
original→copy remains six DoAction tags. No SWFs committed. Compiler/export logs
retain FFDec's host log-file permission warning; commands exited0 and hash/tag/
P-code checks passed. No permission widening was needed for compilation.

## Side-channel pairing and future capture requirement

`parse_combined(raw, tag)` retains actual combined root/side line order; it checks
root sequence via the inherited parser, rejects foreign tagged lines, and treats
other log content as an ordering barrier. Do **not** feed a root-only filtered
`tagged.log` to a future side-channel analysis. Retain the complete append slice,
prelaunch freshness for **both** prefixes and exact main+yihu/player/PID/cleanup
provenance. This slice does not supply a new capture driver.

A direct match requires an adjacent root continuation-prep whose full contiguous
non-AI true-predicate prefix satisfies the unchanged r17 validator, then one exact
side-before/side-after pair with the same saved attribution. Missing/orphan,
duplicate/reversed/interleaved, foreign identity and incomplete prefix fail closed.
Unknown log output between channels is not silently filtered away to make a match.
Local serial/timestamps alone cannot establish a join. No side event fills a hole
in the root sequence or replaces an absent breadcrumb/dynamic-after.

Both CLI modes replay immutable r18: no side markers, original prep-without-
breadcrumb and all incomplete rows retained. Unchanged r05 full-prefix gate exits1
with `Incomplete actor state at clock boundary`. Synthetic matched test cases are
parser tests only; no r19 live observations exist.

## Next live questions (required after this Draft)

Build a fresh-tag copy and adapt the retained physical PID capture to retain both
prefixes with exclusive provenance. Then exercise an actual non-AI true predicate:

- Before + after direct Trace, but no saved-sink breadcrumb: direct source
  continuation/output observed; root-logger channel absent, precise reason unknown.
- Root prep + direct before, no direct after: continued execution/register/output
  availability still unresolved. Do not infer abort or removal.
- Root prep without direct before: even the new pre-goto diagnostic was not
  observed; no native call-entry claim.
- All channels observed: source observation only, not native dispatcher return,
  helper lifetime or later-frame action execution.

Further live is needed because historical r18 has no direct channel. No live in
this slice. Certified ticks, per-edge calibrated OS join, complete initial state/
RNG/trace, deterministic repeat and original/copy noninterference remain separate
unproved requirements. No production closure, merge or deployment.

## Commands

```sh
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r19/build_observer.py --ffdec /tmp/bvn-m0-observer-tools/ffdec/ffdec.jar --output /tmp/bvn-r19-new-copy --run-id UNIQUE_NEW_TAG
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r19/analyze.py
PYTHONDONTWRITEBYTECODE=1 python3.11 evidence/oracle/native-fight-r19/analyze.py --require-oracle
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest discover -s evidence/oracle/native-fight-r19 -p 'test_*.py'
python3.11 tools/verify.py
python3.11 tools/check_handoff.py
```

Tool paths are local examples backed by jar hashes; use the same receipt-pinned
jar elsewhere. Replay/tests use retained repo-relative sources and P-code and
need no surviving temporary copy. Rebuilding always requires a fresh temp output.
