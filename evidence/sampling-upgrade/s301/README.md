# s301 — AFTER-s299 rank #2: Independent ones entry clock

Base: current origin/master `b344582d479980eb397d2e9484862bc7a1d99065`
(s300 #178). Branch: `feat/s301-ones-entry-clock`.
Authority: [AFTER-s299 rank #2](../next-fix-priority-after-s299.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

**Evidence-only, honest-unproved.** No independent all-ten-frame entry facility
is qualified. Fresh ones-only capture stays blocked before launch. Rank 1 and
ranks 3+ are not executed; the s292 diagnosis remains locked, not reopened.

## Bounded facility assessment

[diagnose.py](diagnose.py) pins and replays the complete unchanged
[s292 diagnosis](../s292/README.md), including its historical validator chain.
The same 26,828 events retain 63 selections: four observed joins, 45 selections
of frames without actions, and 14 frame1 windows whose entry remains null.
These are historical observations, not fresh captures or cross-run substitutions.

The new discriminator is whether the preserved glyph placements can supply the
missing all-frame facility without adding action dispatch. The audit decodes the
PlaceObject2 flags/depth/character prefix for all ten original and archived frames,
retaining file offsets and payload hashes. Frame1 has flags6, depth1, glyph1800;
frames2–10 have flags3 (MOVE + character), depth1, glyph1801–1809. None of these
placements carries clip actions. This establishes a static bijection from glyph
symbol to authored frame; it does **not** identify a live entry, count repeated
entries, or resolve the outer ones instance. These offsets are uncompressed file
coordinates, not native dispatch PCs. Full non-action byte equality is inherited
from s292; this prefix decoder is not an interpreter or a new SWF parser.

The second audit joins the exact source call lists to historical endpoint and
entry events, requiring matching run, path, depth, encoded generation and frame:

| Control | Source calls in one callback | Before → after → later frame1 entry sequences |
| --- | --- | --- |
| retained | 2, then 1 | 21647 → 21648 → 21691 |
| encoded retained | 2, then 1 | 22013 → 22014 → 22066 |

Both endpoint states are equal, yet a later frame1 hook event is recorded.
Consequently endpoint equality cannot establish absence of entry or distinguish
the two calls. There is no intermediate frame2 witness, isolated repeated-target
trial, or independently observed dispatch order. This does not claim that any
particular repeated goto dispatches an action. Existing replacement generations
remain helper encodings, not native allocation identity.

[diagnosis.json](diagnosis.json) exposes a ten-row qualification matrix. Every
independent entry/repeated-target/changed-target/replacement/off-on cell is null,
including frame1: an action hook is not an independent observer. The archived
frame1 hook, static glyph-state candidate and added-empty-frame-action candidate
are explicitly rejected as qualified facilities. The last candidate is neither
built nor executed; adding dispatch is not assumed neutral. No live native
resolver has been derived in this slice; this is a bounded rejection of available
archival candidates, not a claim that an independent observer is impossible.

## Gates and next boundary

| Requirement | Exit | Code |
| --- | --- | --- |
| Reproducible archival facility assessment | 0 | `S301_DIAGNOSIS_OK` |
| Independent entry facility | 1 | `S301_ENTRY_FACILITY_UNPROVED` |
| Independent isolated controls | 1 | `S301_INDEPENDENT_CONTROLS_UNPROVED` |
| Ones child clock | 1 | `S301_CHILD_CLOCK_UNPROVED` |

The diagnostic consumes fixed evidence; it is not a runtime trace admission
schema. Changing a flag or filling matrix cells does not create proof.
Before capture, derive an independent live entry and instance resolver covering
all ten frames, preserve original action execution and order, then qualify
separate repeated-target, changed-target and same-depth replacement controls.
Bind selection, entry and next root/callback order on isolated controls, leaving
the natural ones clip untouched. Observer-off/on must retain an independent
observation channel; silence from a disabled helper is not non-perturbation.
Only after these pass is one fresh ones-only capture eligible.

## Source-first boundary and exclusions

1. `scripts/main.json#DefineSprite_1810/frame_1/DoAction.as` is `stop();`;
   frames2–10 have no DoAction. All non-action tags match the archived observer.
2. s292/s282 lock the outer Sprite1813 depth3 placement/removal; this slice
   decodes the inner depth1 glyph placements. MOVE does not prove outer lifetime.
3. The timer selects with gotoAndStop. No synthetic advance, empty-frame action,
   label-end reset or inferred scheduling is introduced.
4. Tests protect actual source prefixes, control order/identity, missing entries
   and nulls, with mutations for wrong depth/MOVE/glyph/clip-action flags,
   cross-run joins and conflated repeated-target claims. No assumed Flash
   schedule is encoded as a regression expectation.
5. Only retained original-player evidence is revalidated. No fresh original or
   Godot comparison exists; parity and mechanism acceptance stay unproved.

Only s301 plus proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest updates
change. No edits under s254–s300, game/scripts, runtime, contracts, shared
sampler/threshold/validator. No synthetic clock, added empty-frame action treated
as neutral, scene/intro repair, HUD reset, cross-run tape or images. Zero new
builds, player launches and captures; no merge, deployment or product closure.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s301/diagnose.py --output /tmp/s301.json
# Each requirement independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s301/diagnose.py --output /tmp/s301-o.json --require-observer
PYTHONPATH=. python3 evidence/sampling-upgrade/s301/diagnose.py --output /tmp/s301-i.json --require-independent-controls
PYTHONPATH=. python3 evidence/sampling-upgrade/s301/diagnose.py --output /tmp/s301-c.json --require-child-clock
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s301 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s292 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s282 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_encoded_digit_lifetime tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape tools.tests.test_sampling_native
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[timing](session-timing.json) retain actual outcomes and measured costs.
[Artifact hashes](artifact-sha256.json) exclude their own index. Initial reading,
future qualification/capture costs and person-days are unknown. Runtime and
contract checks do not apply to this evidence-only change.

Validation: **77 tests pass** (10 new, 12 retained s292, 9 retained s282,
46 retained tools). Archival diagnosis exits 0; all three proof gates exit 1.
Integrity, handoff and diff checks pass. This delivers the evidence slice,
without qualifying the facility or closing M0-02.
