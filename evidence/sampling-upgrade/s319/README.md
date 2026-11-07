# s319 — AFTER-s317 rank #2: Independent ones entry clock

Base: origin/master `4e486b4d9c0764d1abba983c3af8ae4d1bcf6a48` (s318 #196).
Branch: `feat/s319-ones-entry-clock`.
Authority: [unchanged AFTER-s317 table, rank #2](../next-fix-priority-after-s317.md).
Only rank #2 is executed here. Rank 1 delivery stays closed; ranks 3+ stay planning.
The table's “ranks 2+ planning” statement describes s318, not this later slice.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
**Evidence-only, honest-unproved. Independent observation was not derived.**

## Result and boundary

[diagnose.py](diagnose.py) pins and reproduces the entire locked s310 diagnosis,
recursively validating its 26,828 historical events. Ten static glyphs, equal
control endpoints, later frame1 reports and both replacement joins remain prior
results, not new progress. Prior evidence trees and the authority table are unchanged.

The additional bounded result is an exact **observer dependency audit** of four
source members in the locked s274 build archive. It retains member hashes,
source line spans and complete bodies for the three reporters, plus the frame1
and load/unload hooks. It does not compile or install an observer.

| Archived root source | Newly explicit dependency boundary |
| --- | --- |
| line 1, lines 2–7 (`s274Life`) | Root generation starts at zero; load writes `mc.s274Generation` from an incremented root counter. Unload can write the calibration flag. |
| lines 8–12 (`s274Entry`) | Reads helper generation and `aiFight`, can write the retained-entry calibration flag, then reports via `aiEvent`. |
| lines 13–16 (`s274State`) | Reports through the same `aiEvent` sink. |
| report lines 6, 11, 15 | All serialize `String(mc)`, `mc.getDepth()`, `mc.s274Generation`, `mc._currentframe`. These are AS reads of the supplied object, not independently resolved native lifetime/entry data. |

The archived Sprite1810 frame1 hook lexically calls `s274Entry(this)`, then
`s262Init(this,1810)`, then `stop()`. Sprite1813's depth3 load/unload hooks pass
`this` to `s274Life`. This establishes source dependencies only: lexical order
is not native dispatch order, and retained Stop is not proof that helper effects
preserve original execution. Generation and calibration outputs depend on the
instrumentation under qualification. Host custody of these reports cannot turn
that dependence into independent observation.

No independently surviving channel is present in these audited reports when
their shared sink is removed. This is a bounded source finding, **not an observed
observer-off trial**, an exhaustive search of native facilities, or a claim that
an independent observer is impossible. No native entry dispatcher, instance
layout or uninterrupted lifetime resolver has been bound in this slice.

[Diagnosis](diagnosis.json) keeps both live resolvers null and all ten rows of
independent entry/repeated/changed/replacement/off-on qualifications null.
Even frame1 remains unqualified. Fresh capture is blocked before launch; no
controls have been newly run and no mechanism obligation has been closed.

## Required next observation

Bind a channel independent of these helper writes to the actual outer ones
instance lifetime and target-entry dispatch for each frame1–10, including the
nine actionless frames. Qualify isolated same-target repetition, changed-target
entry, same-depth replacement and observer-off/on execution/order comparisons.
Selection, entry and following root/callback boundary must share one run and
independently established instance lifetime. Retain that independent channel in
both observer modes. Only after those prerequisites qualify may one fresh
ones-only capture run. A glyph snapshot, same path/depth, helper counter, logger
silence or filling a JSON cell cannot discharge these requirements.

## Gates and reproduction

| Command requirement | Expected exit | Code |
| --- | --- | --- |
| Fixed-evidence diagnosis | 0 | `S319_DIAGNOSIS_OK` |
| `--require-observer` | 1 | `S319_ENTRY_INSTANCE_RESOLVER_UNPROVED` |
| `--require-independent-controls` | 1 | `S319_INDEPENDENT_CONTROLS_UNPROVED` |
| `--require-child-clock` | 1 | `S319_CHILD_CLOCK_UNPROVED` |
| `--require-fresh-capture` | 1 | `S319_FRESH_CAPTURE_BLOCKED` |

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s319/diagnose.py --output /tmp/s319.json
# Run separately with each proof flag above; every proof requirement exits 1.
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s319 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s310 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s301 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s292 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s282 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_encoded_digit_lifetime tools.tests.test_callback_visual_state tools.tests.test_countdown_phase_tape tools.tests.test_sampling_native
python3 tools/verify.py
python3 tools/check_handoff.py
```

Tests reject altered operands, generation/calibration writes, sink, hook order
and lifecycle receiver, and protect unknown qualifications. They lock archival
source facts and diagnostic honesty, not assumed Flash scheduling.
Actual exits and timings: [gates](gates.json), [checks](project-checks.json),
[timing](session-timing.json). [Scope](scope-audit.json), [manifest audit](manifest-audit.json)
and [artifact hashes](artifact-sha256.json) record custody. Artifact index excludes
itself and Python caches. Initial reading/design and person-days are unknown;
measured implementation time excludes subsequent commit/push/PR work.

## Source-first and exclusions

1. `scripts/main.json#DefineSprite_1810/frame_1/DoAction.as` is `stop();`;
   frames2–10 have no actions, as locked s292 byte audit confirms.
2. Inner glyph depth1 placement flags are 6 on frame1 and 3 (MOVE + character)
   on frames2–10. Outer Sprite1813 depth3 lifecycle is a separate identity
   obligation; the duplicate control is not the natural ones instance.
3. Timer uses `gotoAndStop`; no inferred playback clock or label-end reset.
4. Tests protect source provenance and unknowns, not invented entry timing.
5. Historical original-player evidence is revalidated only. No fresh same-input
   original/native comparison exists here; parity remains unproved.

Only new s319 files plus minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking
updates change. Zero-byte diffs for game/scripts, runtime, contracts, shared
sampler/threshold/validator and all s254–s318 evidence. No static glyph-as-entry,
synthetic clock, empty-frame action treated as neutral, scene/intro repair,
cross-run images/tape or HUD reset. Zero builds, player launches, captures or
images. No re-ranking, other-rank execution, deployment, ready marking or merge.

Validation result: **95 tests pass** (8 s319, 41 retained slice tests, 46 shared
tool tests). Base diagnosis exits 0; all four proof flags exit 1. Integrity,
handoff and whitespace checks exit 0. These are audit checks, not live proof.
