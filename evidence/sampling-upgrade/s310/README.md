# s310 — AFTER-s308 rank #2: Independent ones entry clock

Base: origin/master `38f66b5cb46df0fab2010f30ea4f423072c1d7b6` (s309 #187).
Branch: `feat/s310-ones-entry-clock`.
Authority: [AFTER-s308 rank #2](../next-fix-priority-after-s308.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
**Evidence-only, honest-unproved. No independent live resolver was derived.**
Only rank #2 is executed; rank 1 and ranks 3–9 remain outside this slice.

## Result and limits

[diagnose.py](diagnose.py) pins and reproduces the complete locked
[s301 diagnosis](../s301/README.md), recursively revalidating its historical
26,828 events. Static ten-glyph mapping, equal endpoints, later frame1 hooks
and all ten rows of unknown qualification cells remain unchanged. Replaying
these facts is validation, not a new entry-clock result.

The additional bounded audit joins **both replacement controls**, previously
retained as encoded lifecycle observations, to their exact source blocks and
before/unload/load/after events. It checks same-run custody, event order,
path, endpoint depth, helper generation and frame consistency. It preserves
all observed depths, without mapping the unload value to the endpoint slot.

| Control | Before → unload → load → after sequences | Helper generation | Endpoint / unload depth | Observed frames |
| --- | --- | --- | --- | --- |
| replacement | 21737 → 21783 → 21784 → 21831 | 2 → 3 | 100001 / -132770 | 1 only |
| encoded replacement | 22114 → 22168 → 22169 → 22218 | 3 → 4 | 100001 / -132770 | 1 only |

Both source blocks remove and duplicate `__s274Control` at depth100001;
neither explicitly selects a target with gotoAndStop. The second also removes
the replacement at tick8, outside its before/after bracket. That event remains
in the locked predecessor; it is not substituted for a replacement witness.
The audit does not interpret the negative unload depth as native memory,
allocation reuse, a normalized slot, or proof of either instance continuity or
replacement. These are archived instrumented helper reports, not independent
native identities. Frames2–10 have no replacement entry witness here. Even
frame1 has no independent observation or observer-off/on comparison.

This closes no mechanism obligation. The new join makes the available
replacement evidence and its limitations reviewable; it does not fulfill the
requested live facility. No native entry dispatch address, outer-instance
layout/generation resolver, or independent observation channel has been bound.
The rejection is bounded to available locked evidence, not a claim that such a
facility is impossible. [Diagnosis](diagnosis.json) retains null live resolvers,
entry/order/off-on witnesses, and the ten-row qualification matrix.

## Qualification boundary

Before any fresh ones-only capture, an independent channel must bind the live
outer ones instance and target entry for **each frame1–10**, including frames
with no DoAction. It must distinguish isolated same-target repetition from
changed-target entry, and same-depth replacement from retained identity.
Each selection, entry and following root/callback boundary must share one run
and independently established instance lifetime. No static placement coordinate
is a live dispatch address; no helper stamp is an allocation identity.

Observer-off/on trials must retain the independent channel in both modes and
compare original action execution and order. Disabling the only logger and
seeing silence cannot prove preservation. Only after these controls qualify may
one fresh ones-only capture run. No new controls or captures ran in s310.
The fixed-evidence diagnostic is not an accepting trace schema: filling a JSON
cell or changing a proof flag cannot qualify an observation.

| Requirement | Exit | Code |
| --- | --- | --- |
| Reproducible historical witness audit | 0 | `S310_DIAGNOSIS_OK` |
| Independent all-frame entry/instance resolver | 1 | `S310_ENTRY_INSTANCE_RESOLVER_UNPROVED` |
| Isolated repeated/changed/replacement/off-on controls | 1 | `S310_INDEPENDENT_CONTROLS_UNPROVED` |
| Independent ones child clock | 1 | `S310_CHILD_CLOCK_UNPROVED` |
| Fresh capture eligibility | 1 | `S310_FRESH_CAPTURE_BLOCKED` |

## Source-first and scope

1. `scripts/main.json#DefineSprite_1810/frame_1/DoAction.as` is `stop();`;
   frames2–10 have no actions. Locked s292 verifies original and archived
   non-action timeline bytes. No empty-frame action is added.
2. Inner glyphs are depth1: frame1 flags6, frames2–10 flags3 (MOVE + character).
   These do not resolve the outer ones instance. The outer Sprite1813 depth3
   placement/removal stays locked in s282/s292. Duplicate control helpers are
   separate from the natural ones clip and cannot replace its lifetime proof.
3. Timer selection uses gotoAndStop; no inferred playback advance or label-end
   reset is introduced. Source replacement blocks remain exactly preserved.
4. Tests protect actual historical custody/order/identity fields and reject
   missing, duplicate, cross-run, wrong-generation/frame/path/depth witnesses.
   They assert no assumed Flash schedule or synthetic entry clock.
5. Only historical original-player observations are revalidated. There is no
   fresh original/Godot comparison; implementation and parity remain unproved.

Only s310 plus proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest updates
change. No edits under s254–s309, game/scripts, runtime, contracts, shared
sampler/threshold/validator. No static glyph-as-entry, synthetic clock, added
empty-frame action treated as neutral, scene/intro repair, HUD reset, cross-run
tape or images. Zero builds, player launches, captures and images. No other
ranks, merge, deployment or production admission; M0-02 remains pending.

## Reproduce and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s310/diagnose.py --output /tmp/s310.json
# Each proof flag independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s310/diagnose.py --output /tmp/s310-o.json --require-observer
PYTHONPATH=. python3 evidence/sampling-upgrade/s310/diagnose.py --output /tmp/s310-i.json --require-independent-controls
PYTHONPATH=. python3 evidence/sampling-upgrade/s310/diagnose.py --output /tmp/s310-c.json --require-child-clock
PYTHONPATH=. python3 evidence/sampling-upgrade/s310/diagnose.py --output /tmp/s310-f.json --require-fresh-capture
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s310 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s301 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s292 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s282 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_encoded_digit_lifetime tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape tools.tests.test_sampling_native
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [timing](session-timing.json) and
[artifact hashes](artifact-sha256.json) record actual outcomes. Hash index
excludes itself. Initial reading/design and person-days are unknown; measured
implementation time does not include later commit/push/PR work.
No runtime or contract change requires those additional suites.

Validation: **87 tests pass** (10 focused, 10 retained s301, 12 retained s292,
9 retained s282, 46 retained tools). Archival diagnosis exits0; all four proof
gates exit1. Integrity, handoff and whitespace checks pass. Delivery of this
evidence slice does not qualify the observer or complete M0-02.
