# s252 — Rank 4: AS call exit / receiver ownership

Baseline `5bd0d797`, branch `feat/s252-as-call-exit`. Exclusive s252, absent at
start. This is an **evidence-only slice with one fresh native capture**, using
the unchanged s76 Chad attack/neutral/ground/near tape and existing s245 probe.
`production_admitted=false`; `native_parity_proven=false`; M0-02 stays pending.
No production code, observer, exit model, validator or obligation changes.

## Decision and new observation

The thin observation is justified: the original normal-attack goto changes the
parent timeline across the tracked controller's authored lifetime. A fresh run
on the requested master tip reproduces the gap. **No exit-model fix is proved.**
Removal remains an observed lifecycle fact, not a witnessed VM return or abort.

| Boundary | Sequence / tick / display | Observation |
| --- | --- | --- |
| Original call front edge | 7162 / 10 / 430 | `call_before`, selected invocation began at 7159 |
| Independent observer armed | 7163 / 10 / 430 | `instance255`, depth -16353, parent frame 5, same occupant |
| Callee entry | 7164 / 10 / 430 | Same receiver and occupied depth |
| Original goto front edge | 7170 / 10 / 430 | Same receiver and occupied depth |
| P1 outer clip callback | 7173 / 10 / 430 | Parent body already at frame 183 |
| Independent root sample | 7185 / 11 / 431 | Depth empty; saved receiver string empty; saved parent/frame undefined |

There are no `goto_after`, `callee_exit`, or `caller_after` events. The complete
27-event boundary window, including unrelated callbacks and input/state events,
is retained in `diagnosis.json.gz`; the entire raw capture is retained untrimmed.
The parent reaches frame 183 within the same display period, but receiver loss
is only directly sampled at tick 11. This does not locate the exact removal PC.

New static cross-check: the **built, captured Chad SWF** was exported as P-code.
The original goto `CallMethod` is followed by `Pop` and the emitted `goto_after`
observer call, before `wankai()`. Both goto-side markers use the same register
operands (`register1` receiver / `register3` observer host). The caller's original
`CallFunction doAllAction` is followed by the emitted `caller_after` lookup/call.
The compiler did not omit these markers. Full selected P-code blocks retain
their original paths under `pcode/`; tool/input/output hashes and command are in
`pcode-provenance.json`. Static instructions do **not** prove executed PCs.

The existing observer already saves root, receiver, parent, depth and path in
`_global`, with a separate armed boolean. Its gate uses saved-root tick 10–11;
it does not require the removed receiver to remain truthy. Root tick 11 logs
successfully despite the invalidated reference. Simply changing `_root` to a
saved root is therefore not a demonstrated fix. Remaining ambiguity includes
suppressed continuation versus execution reaching an observer path that fails
to emit. No positive observation distinguishes those models here.

## Source-first scope and separate ownership symptom

1. The exact caller is Chad
   `DefineSprite_607/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`.
   It evaluates `gameRunning()` once then calls unqualified `doAllAction()`.
   Callee `DefineSprite_16/frame_1/DoAction.as::doAllAction(special)` has the
   normal-hit goto followed by further predicates and `doDropDown()`, with no
   explicit return. The complete function is retained, not just the goto line.
2. Hash-checked s72 source XML independently recomputes the s245 facts: new
   Sprite16 at depth31 on Sprite607 frame1, removal at frame13, `砍1` at frame183.
   `diagnose.py` checks SWF, locked script and XML hashes. A jump to 183 is not
   evidence that frame13 scripts execute. This bounded controller investigation
   does not claim a complete move-frame audit or authorize runtime changes.
3. The observed authored exit from the parent label is conditional
   `_parent.gotoAndPlay("砍1")`; that is distinct from an AS function return.
4. Tests retain missing exits and reject missing markers, changed identity and
   broken raw sequences. They never assert that removal means return.
5. One fresh original-player capture uses the unchanged tape. Its 122 fight
   actor-state payloads equal both s76 and s245 exactly. This native/native
   comparison is neither Godot parity nor proof of zero timing perturbation.

s247 is separately recomputed from its retained raw capture: all three lists
and stamps are intact, while direct-parent `pn` and computed target are undefined
at ticks16–18. The projectile handler's parent is the fighter; nested `mian`'s
parent is the projectile. Function presence in the structural walker does not
prove gameplay receiver eligibility. Its observed grandparent `pn=2` does not
authorize ancestor substitution, receiver exemption or an exit-model change.
No Yulong capture, s241–s244 work, or ranks1–3 are reopened.

## Gates and remaining proof

| Check | Exit / result |
| --- | --- |
| Fresh native receipt | 0; 9,423 events, 61 root samples, 122 actor states |
| Chad exit boundaries | 1; three missing exit markers |
| Selected call-site gate | 1; 439 complete (394 false / 45 true), one incomplete |
| Full AS gate, separately executed | 1; 594 unvisited, 415 uninstrumented |
| Three-capture raw/source diagnosis | 0; all 122 fight states equal |

s76 had 396 false invocations and s245 had 397; s252 has 394. Pre-fight counts,
display offsets and instance names differ and are preserved. Instances are joined
within a capture, never by requiring `instance257` across runs. Historical raw
streams are revalidated against their original metadata; old receipts are not
resealed with current probe hashes. Old negative tests remain unchanged.

Before selecting an exit model, obtain a **positive continuation discriminator**:
for this exact source-bound call only, observe whether the first post-goto
instruction and the observer entry are reached independently of removed-target
property resolution and observer guards. A bounded probe-owned counter/object
captured before the call and read from the surviving root, or an executed-PC
facility in the original player, would need its own identity and compilation
proof. Preserve the unqualified call, predicate count, goto, input tape and
existing markers. A missing new marker alone must still not be called a return.
No such discriminator or VM-exit proof is claimed by this PR; zero AS obligations
are closed. Full AS ownership, dynamic dispatch, other branches, nested receiver
eligibility, static-loader runtime identity and native/Godot parity remain open.

## Reproduction

Build and capture commands are in `capture-environment.json` and the fresh
`native-build.json`. The build uses existing `--chad-lifecycle`, no new flag.
Restore `native-build.tar.gz` into `/private/tmp/bvn-s252-build-r01`, raw gzip
into `/private/tmp/bvn-s252-capture-r01/native.log`, and the original receipt into
that directory as `receipt.json`. Do not rewrite receipt paths or hashes. Gates
record exact commands and measured subprocess durations in `gates.json`.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s252/diagnose.py
python3 -m unittest tools.tests.test_call_exit_diagnosis
python3 tools/verify.py
python3 tools/check_handoff.py
```

The diagnosis needs only repository artifacts, including s72's XML archive.
P-code can be regenerated with the recorded JPEXS command after restoring the
build. Capture used the shared native lock and one player launch; the sandbox
preflight rejected `ps` before launch, then authorized escalation succeeded.
An initial negative test hardcoded the old instance name and therefore failed
to mutate the fresh capture; it now derives that name from the actual observation.
The failed test output is retained. No collector or gate was adjusted.
Final check results and measured wall time are in `project-checks.json`,
`focused-tests.json` and `session-timing.json`. No merge, deployment or gameplay.

Final verification: **99 focused tests pass**, including retained Chad/Yulong
negatives and sampling/import guards. Integrity, handoff and contracts each
exit **0**. Receipt exits **0**; lifecycle, selected call-site and full AS gates
remain **1**. All earlier evidence/tapes and admission flags are unchanged.
