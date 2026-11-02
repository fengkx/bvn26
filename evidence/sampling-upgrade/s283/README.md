# s283 — Body-push observer qualification (evidence-only, unproved)

Base: master `d840168c4c70e170d2a443844e508d0a66b53739` / #160.
Branch: `feat/s283-body-push-call`. Exclusive authority:
[AFTER-s281 rank 2](../next-fix-priority-after-s281.md).
`production_admitted=false`; `native_parity_proven=false`;
`observer_qualified=false`; `external_callsite_execution_proved=false`.
M0-02 remains pending; zero product obligations closed.

The scope is P2 base Sprite638 `on_enterframe`, ticks10–12, on the retained
s64/s264 tape. No other priority is executed. No native player was launched:
the candidate fails the qualification prerequisite, so a capture is not justified.

## Proved and unproved

The original function's complete exported bytecode proves that both body-air
and displacement guards use `PushDuplicate`/conditional jumps, not eager `And`.
The target `_root.game["p" + pn].mc.bdmn` is evaluated before receiver `bdmn`,
followed by the one original `CallMethod hitTest`. Unlike s275's eager `Or`,
short-circuiting here is now bytecode-backed, not inferred from source syntax.
This proves static evaluation order only, not which branch ran at ticks10–12.

The [diagnosis](diagnosis.json) retains **every opcode and operand**, function
flags, all branch destination indices, fallthrough edges and explicit returns
for both original and candidate. Push packing and integral numeric spelling
are normalized; strings, register numbers and function flags are not erased.
The original/candidate full-frame exports are retained as compressed evidence.
FFDec prints the terminal address on the next function definition; extraction
retains that exact address as the selected function's exit label. Missing or
unknown branch labels reject rather than being guessed to mean return.

The candidate wraps the existing guards and receiver/target/result expressions,
with one source `hitTest` and an explicit `this` owner argument for eventual P2
filtering. It changes no source outside this callback. However, recompiling
changes `DefineFunction2` register count **12 → 13**, preload flags and register
allocation. A complete correspondence between the two activations/registers
and an observer-erasure proof have **not** been established. The complete diff
is retained, including expected observer instructions. A nonempty diff is not
itself proof of semantic inequivalence; this result is conservative rejection
of an **unproved** candidate, not a discovered gameplay bug.

This is a compile-only candidate, not a usable capture build. The helper is
intentionally not installed, the candidate SWF must not be launched, and there
is no claim that P2/tick filtering, logging perturbation or once-evaluated live
operand lifetimes have been qualified. Successful compilation does not pass
those gates. In particular, source expression counts cannot prove dynamic
once-only evaluation. No helper implementation or runtime fix is admitted.

The unchanged s273 analyzer also revalidates all **5,437** s264 events, P2
sampled frames **4/5/6** at ticks10/11/12 and the initialization boundary.
The external call's execution remains **null / unobserved**, not false. These
historical snapshots cannot supply the missing guard, operand or result rows.
The retained missing P1 receiver at tick11 is not exempted or initialized early.

## Source-first boundary

1. [s273's complete callback/caller and frame4–7 map](../s273/diagnosis.json)
   remain locked; this slice adds whole-function opcode/control-flow evidence,
   including preceding side effects and subsequent movement/returns.
2. The locked wrapper places Sprite638 at depth1, new PlaceObject. Body bdmn
   placement and P1 initialization are retained in s273/s264; source placement
   is not an observed operand lifetime or native allocation identity.
3. All explicit early returns, jumps and conditional goto/play instructions
   remain in the graph; the terminal address is not an invented label-end reset.
4. Tests assert original bytecode guards/operand order, complete branch
   resolution, one hitTest, unchanged source outside the callback, and unknown
   execution. They do not require a guessed collision result.
5. The historical same-input run is replayed, not recaptured. It has no external
   callsite events. No native parity or receiver-eligibility fix is proved.

## Next bounded discriminator

Prove a full activation/register mapping and observer erasure, or use a
qualified stack-preserving bytecode insertion retaining original activation.
Then qualify a helper limited to this P2 body and ticks10–12, including actual
early-exit/guard outcomes, once-evaluated operands/result and same-run lifetime
boundaries. Only after that prerequisite should one unchanged s64 capture run,
with natural executed/skipped controls (or an honest missing-control result).
No extra hitTest, receiver exemption, early initialization, tick41, blanket
collision coverage, forced branch or production implementation is authorized.

## Reproduction and costs

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s283/diagnose.py --output /tmp/s283.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s283/diagnose.py --output /tmp/s283-required.json --require-observer # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s283/diagnose.py --output /tmp/s283-call.json --require-external-callsite # exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s283 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gate commands and costs](gates.json) include 10 new tests and 65 retained
focused tests; diagnosis passes, both new proof requirements and the unchanged
s273 external-callsite requirement exit1. [Project checks](project-checks.json)
record integrity and handoff. No contracts change.

[build_probe.py](build_probe.py) reproduces the compile-only experiment using
JPEXS 26.2.1 (`--output` must be a new temporary directory; `--ffdec` points to
its jar). It writes only s283 evidence and that temporary directory. The original
SWF is read-only. [build-audit.json](build-audit.json) pins tool/input/output
hashes, all three commands and measured subprocess times for the retained build.
The full-frame exports permit portable extraction checks without Java.

There were two successful candidate compiles and five script-only exports:
an initial original export, then original/candidate exports per compile. The
first extraction omitted FFDec's external terminal label and the analyzer
correctly rejected an unresolved branch; the second retained that address.
Initial download/setup/first compile/export costs were not retained; they are
unknown, not zero. No failed native capture, new images, or native launch occurred.
[Session timing](session-timing.json) separates measured costs from unknown
setup and person-days. Temporary tools, SWFs and console logs stay outside the
repository; only bounded analysis evidence is retained.

Only s283 and the four requested tracking files change. s254–s282, original
inputs, runtime/contracts, shared samplers/validators and thresholds remain
unchanged. No receipt resealing, merge, deployment or production-ready claim.
