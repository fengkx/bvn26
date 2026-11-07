# s323 — AFTER-s317 rank #6: terminal callback channel

Base: origin/master `78bf16cff0f568d65f3a12c131a4839176371f19` (s322 #200).
Branch: `feat/s323-terminal-callback`.
Authority: [unchanged AFTER-s317 rank #6](../next-fix-priority-after-s317.md).
Only rank 6 is executed; ranks 1–5 deliveries remain closed, ranks 7+ planning.
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

## Outcome and new evidence

The independent loaded-body/owner-generation/activation entry-to-dispatcher-return
channel is **not established**. No live invocation is independently observed.
This delivery bounds the applicability of retained observer tooling to the one
archived root `onEnterFrame` instrumentation callback from s314. It does not
complete the rank-6 mechanism or execute the full terminal callback inventory.

The complete locked s314 diagnosis is reproduced, including the untrimmed
normal/held suffix and serializer audit. Those results and solved independent
custody pair are retained validation, **not new progress**.

The new [diagnosis](diagnosis.json) retains source locations and implementations
for four candidate observer paths. A pure text transformation applies the exact
retained `instrument_schedule` function to the archived callback-installing
frame action; nothing is compiled, installed or executed in a player.

| Candidate | Source-bound applicability result |
| --- | --- |
| schedule | Enter/exit text surrounds the whole frame action assigning `onEnterFrame`. The archived action is unchanged between the markers. Neither marker is inside the assigned closure, so this does not observe callback entry/return. |
| DoAction / clip entry | Inventory explicitly excludes `game/main.swf`; this target is a DoAction and remains unchanged. A block entry would still not observe the entry of its assigned function. |
| callsite | The reviewed fighter handler selector does not select this root callback. Its `call_after` and `end` markers are inside the selected handler, not at its outer dispatcher continuation. |
| BODY callback | Fighter-only hooks surround `on_enterframe();`. The exit is after that inner call and still inside the enclosing clip callback. Slot/coordinates do not identify closure owner generation or activation. |

All four candidate emitters depend on `_root.aiEvent`, the property the closing
guard replaces. No independent replacement-surviving sink or binding is
established. Source ordering is conditional evidence only: it does not prove
that quit resumed, that replacement executed, or that any invocation returned.
This search is bounded to these retained paths and s314, not a claim that no
external facility exists. The dry transformation uses an archived patch with
an explicitly non-live SWF identity placeholder; it does not construct an
original-byte or loaded-body attestation.

## Unproved boundary and next prerequisite

All five s314 qualified witnesses remain null: loaded body, owner/defining-scope
and closure generation, activation entry, matched dispatcher return, and
observer-off/on preservation. No host timestamp, source hash, event sequence,
receiver spelling, body-end marker or silence can fill those fields.

A future facility must resolve one live closure and its owner generation,
identify each invocation independently, and retain the same invocation through
logger replacement to the dispatcher continuation. Done-producing and closing
invocations must remain distinct. Normal return, unwind and process termination
need different outcomes. Qualify observer-off/on effects before fresh capture;
full inventory remains deferred even if this one callback later qualifies.
This package accepts no external trace or proof override and supplies no live
resolver. Missing qualification blocks capture; the solved pair is not recaptured.

## Source-first and scope

1. The full archived frame action and serializer remain pinned in s304/s314;
   this slice additionally binds the retained observer implementations.
2. No placement, MOVE, instance lifetime or game mechanism is changed.
3. No source exit is promoted to native return; assignment, inner-call return,
   outer dispatcher continuation, quit and unwind remain distinct.
4. Tests protect source applicability, locked inputs and false proof gates.
5. Historical captures are revalidated only; no new original/Godot comparison.

Only s323 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
Authority table and s254–s322 remain byte-identical. No runtime, contracts,
shared sampler/threshold/validator, game/ or scripts/ change. No fixed suffix
threshold, silence-as-return, trimming, random tape changes, receipt resealing,
full-AS claim, re-ranking, other-rank experiment, build, launch, attach, memory
read or capture. No deployment, ready marking or merge.

## Gates and reproduction

| Mode | Expected exit |
| --- | --- |
| Base diagnosis (`S323_DIAGNOSIS_OK`) | 0 |
| `--require-independent-channel` | 1 |
| `--require-logger-replacement` | 1 |
| `--require-callback-completion` | 1 |
| `--require-terminal-completeness` | 1 |

Proof flags emit distinct `S323_*_UNPROVED` codes; changed locked inputs emit
`S323_EVIDENCE_INVALID`, not a successful audit or a proof result.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s323/diagnose.py --output /tmp/s323.json
# Repeat with each proof flag above: expected exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s323 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) and [project checks](project-checks.json) record actual commands,
exits and durations. [Input hashes](input-sha256.json) pin authority, prior and
candidate tooling; s314 recursively checks earlier inputs.
[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json),
[timing](session-timing.json), and [artifact hashes](artifact-sha256.json) retain
scope and packaging evidence. Artifact index excludes itself and caches.
Initial reading/design and person-days are unknown; measured implementation
excludes subsequent commit/push/PR work. Green package checks do not prove a
live channel or product parity.

Validation: **107 tests pass**. Base diagnosis exits 0; all four proof gates
exit 1 with their UNPROVED codes. Integrity, handoff and whitespace checks exit 0.
