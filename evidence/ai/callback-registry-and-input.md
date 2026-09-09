# Shared callback registry and verified reference input

Status: partial source port, not whole-match parity. The current reference is
`input-alias-r12`, whose per-read input delivery is verified. Earlier captures that
attempted to overwrite `Key.isDown` are historical diagnostics, not verified
fixed-input runs. Their files and random tapes remain unchanged.

## Callback semantics and implementation

The minimal nested ClipAction probe is built with:

```bash
python3 tools/probes/build_callback_registry_probe.py --ffdec /absolute/path/to/ffdec-cli.jar --output /tmp/fresh-registry-probe
python3 tools/probes/check_callback_registry.py
```

The captured source hashes, output hash, complete log and checked callback order are
under `evidence/probes/schedule/callback-registry/`. The probe has two parents, each
with a child. Parent and child both have placement ClipActions, matching the game
BODY/controller event mechanism. Each child receives an instance token in its first
DoAction. The probe distinguishes retained instances from reconstructed ones.

- Initial registration produces B.child, B.body, A.child, A.body callbacks.
- Retained forward/backward goto preserves tokens and callback order.
- Removing and recreating A.child yields token 3 and A.child, B.child, B.body, A.body.
- Swapping parent display depths changes the logged depths but not callback order.
- Recreating B.child yields token 4 and B.child, A.child, B.body, A.body.

These observations require ordering across subtrees. `SourceCallbackRegistry` owns
monotonic registrations with weak targets. A dispatch snapshots the reverse order;
removal invalidates pending entries, and new registrations wait for a later display
tick. `AiControllerInstances` registers/unregisters compiled callbacks on source
placement membership changes. CPU source-frame notifications now synchronize at
the actual goto/advance, with the tick prepared before timeline advancement.

Main registers both BODY callbacks and their compiled children in the shared queue.
The initial P1/P2 registration order matches the current post-load slice; full
asynchronous boot/loading order remains unverified. Helpers/effects and the remaining
legacy player controllers have not all migrated into this queue. Player non-hurt
input remains a legacy callback before its BODY, not a completed source controller
port. The unused non-hurt templates in player BODY metadata remain gated off.

Original `frame_1` declares `var hits = 0`. The state compiler now includes this
write, and native hit count/HUD reset at source-frame execution, not an earlier
enterFrame check. Compiled BODY owns hurt falling, so the legacy hurt-fall counter
cannot resume after source recovery and incorrectly re-enter knockdown.

`input-alias-r12` sequence 4414 executes P1's pre-existing frame 8 script; sequences
4419 and 4421 then execute callback-goto targets P2 frame 20 and P1 frame 1. Main now
captures each initial frame-queue length before callbacks, preserving this separation
from targets added during enterFrame. The root observer phase is still provisional;
frame-boundary comparison does not certify the entire world update order.

## Input capture correction

The FP32 `Key.isDown` property does not accept the attempted function replacement.
The minimal `key-hook` probe records all of the following:

```text
global_same = true
global_read = false
body_alias_read = false
direct_alias_read = true
```

Source, output and tool hashes plus the log are retained in
`evidence/probes/schedule/key-hook/`; its source lives under
`tools/probes/as2/key_hook/`. Rebuild the one-frame base with the command recorded
in `build.json`, then import that source directory with FFDec `-importScript`.

The original BODY load ClipAction assigns `var kis = Key.isDown;`. The analysis-only
game copy now binds that alias to `_root.aiKeyDown`, leaving the game predicates,
key arguments and source control flow intact. The hook records the receiver, key
code and returned boolean for every read. The bootstrap records the configured
key codes and each input-state update. The collector scans actual event order and
rejects reads inconsistent with the current input state, including a stuck release.
It does not infer delivery from elapsed display ticks or a claimed input intent.

The original r12 capture completed 600 fight frames, with 13,971 events and 3,132 key
reads. All reads matched intent. Positive reads reached P1 for right (20), attack
(9), down (125), and ranged (2). Jump/special/summon intents need not be read while
their source control windows are unavailable; the report does not claim they were
executed. The terminal HP values are P1=742 and P2=950. This is evidence that input
reached original character code, not that the native combat is correct.

## Native verification and remaining difference

The registry, instance lifecycle, CPU driver, projectile birth/lifetime, repeated
match teardown, source hit settlement and Vs Com/KO tests pass. The capture collector
has five passing boundary/input tests. Some native runs still report ObjectDB/resource
warnings at exit; no complete resource-lifetime acceptance is claimed.

The new reference's first loaded poll is P1 frame 3, P2 frame 2. The replay can now
seed frame 2 from its valid predecessor frame 1, already initialized by setup.
Frame 1 itself remains rejected because its predecessor would require loop/goto
reconstruction. This is still a single partial post-load checkpoint, not boot replay.

Before the initial/deferred-frame fix, the r12 native replay first differed at
boundary 465. After the fix, boundaries 1–498 match and 499 differs: original P2
frame 13 versus native P1 frame 13, at source display 552. Across 362 snapshots per
fighter, relative displacement deltas are zero, but P1 facing has a 200-point xscale
difference. Therefore even the compared interval does not establish complete parity.
Random and clock failure fields are empty; full tape completion is not claimed.

The source `doAllAction` repeats gotoAndPlay("走") while movement is held, whereas
the legacy player path only starts walking on action change and allows its playhead
to reach frame 13. This is the next source-controller gap to address through the
compiler, not by changing this reference's frames, inputs or thresholds. Preserve
the full objective: fixed Naruto versus easy Ichigo, complete playable match and
same-input behavior, not merely a passing subset of boundary fields.
