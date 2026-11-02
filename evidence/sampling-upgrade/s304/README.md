# s304 — AFTER-s299 rank #5: terminal callback ownership

Base: origin/master `1afd619632badbc68ec985fdfbc9bf85a8a7fdc4` (s303 #181).
Branch: `feat/s304-terminal-callback`.
Authority: [AFTER-s299 rank #5](../next-fix-priority-after-s299.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

The locked [s293 diagnosis](../s293/README.md) reproduces exactly. Independent
normal/held host custody is proved and remains closed. This cut bounds **one
archived observer-source callback**, the root `onEnterFrame` assigned in
`patches/main/frame_10/DoAction.as` inside s293's held build archive. It is an
instrumentation callback, not an asserted authored gameplay callback. Its full
source, SHA-256, line coordinates, exits and complete terminal suffix are derived
in [diagnosis.json](diagnosis.json) by [diagnose.py](diagnose.py).
No source-text boundary is claimed as an observed native entry/return.

## Bounded source and terminal evidence

The root frame-10 action installs this function on the root callback property.
Its body enters before the completion guard. On the done-producing branch,
`done` precedes setting `aiS284DoActionComplete=true`; the timeout conditional
still follows, then the function can fall through. There is no return marker.
The next invocation's guard emits `capture_window_closed`, replaces the root
callback with an empty function, replaces `aiEvent` with an empty function,
requests `fscommand("quit")`, and only then reaches the explicit `return` if
execution resumes. The timeout path separately requests quit before possible
fallthrough. The marker precedes these operations; it does not observe their
completion. Replacing a property does not demonstrate return of its active
invocation. The assigned source owner is known; live closure identity, defining
scope instance/generation and activation identity are absent.

Held `done` is sequence5514 at display495/tick60. The archive retains every
sequence5515–5549: 34 key reads and the closing marker. The first 16 reads carry
P2 receiver text, then 16 P1 reads, then one P2 and one P1. These are receiver
strings, not callback identities or closure generations. No gameplay callback
is assigned ownership of these rows. Closing at the same tick/display is
explained by guard-before-increment placement; it is not a scheduler drain.
Normal has no suffix after done. That remains quit truncation, not completion.
Counts describe this archive only; **no fixed 34-read threshold** is introduced.
Neither more reads nor silence can fill an absent return witness.

## Missing independent witness and gates

Before any further capture, qualify an observation facility independent of the
logger that the closure disables. It must bind exact loaded callback body,
owner generation and activation identity at entry, and match the same activation
returning to its dispatcher after the relevant marker. An unwind or process
termination must be classified separately from a normal return. Defining scope
and callback replacement must not be inferred from a receiver string. Qualify
observer-off/on preservation before using the facility as evidence.

For **every** terminal callback, a further complete dispatch/pending inventory
with matched exits is necessary, including callbacks that make no key reads.
One root callback return alone would not establish terminal completeness.
Those independent observations are absent here, not inferred from source or
host equality. No capture is attempted before qualification.

| Gate | Exit | Code |
| --- | --- | --- |
| Reproducible bounded diagnosis | 0 | `S304_DIAGNOSIS_OK` |
| Selected callback completion | 1 | `S304_CALLBACK_COMPLETION_UNPROVED` |
| Every terminal callback complete | 1 | `S304_TERMINAL_CALLBACK_COMPLETENESS_UNPROVED` |

## Source-first and exclusions

1. The complete selected callback source is retained with line bounds, including
   guard, ordinary fallthrough and timeout; no gameplay mechanism is changed.
2. No PlaceObject/MOVE or instance lifetime changes; a callback-property write
   is not evidence of a clip's removal or its active invocation's return.
3. Root gameplay scene goto precedes callback installation. No gameplay label
   end, stop/goto or timeline fallthrough is synthesized; quit is not a return.
4. Tests protect source ordering, archive custody and absence of proof under
   arbitrary synthetic suffix lengths; synthetic tests are not native evidence.
5. The unchanged s293 archived input/captures supply the native observations;
   no fresh original/Godot comparison or native parity claim is made.

Only s304 plus proportionate tracking/manifest updates change. No edits under
s254–s303, game/scripts, runtime, contracts or shared sampler/threshold/validator.
No ranks1–4 or6+, recapture of the solved pair, trimming, random tape replacement,
receipt repair/resealing, full-AS claim, merge or deployment. The existing random
and coverage gaps remain in the reproduced locked result. No new builds,
launches or captures. This delivered evidence slice does not complete M0-02.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s304/diagnose.py --output /tmp/s304.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s304/diagnose.py --output /tmp/s304-one.json --require-callback-completion # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s304/diagnose.py --output /tmp/s304-all.json --require-terminal-completeness # exit1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s304 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s293 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s284 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates and tests](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest changes](manifest-audit.json) and
[timing](session-timing.json) record executed validation and costs. Initial
reading/design and person-days are unmeasured. No runtime/contract change needs
Godot or contract checks.

Validation: **90 tests pass** (9 focused, 17 retained s293, 10 retained s284,
54 retained tools). Diagnosis, integrity and handoff exit0; both completion
proof gates exit1 as expected.
