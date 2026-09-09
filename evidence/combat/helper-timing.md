# Helper repeat-contact and duration correction (2026-09-09)

Scope: the reported short Gaara O assistance, the shared Kon contact path, and
source-derived recovery timing. Original `game/` and `scripts/` are unchanged.
The user requested source analysis and regression first, then native Flash
validation. Full game, pixel, audio and browser parity are not asserted.

## Source-first audit

- Gaara root scripts: 1 parks/stops; 2 plays and creates fzccXg; 13 action=1;
  16 bsd(pn,"XG_fzbs",true); 38 bsw(pn); 44 shine and load-time target X;
  85 fzccXg, then natural wrap to frame 1. All other root frames have no script.
  Sprite 48 stops at its empty frame 33. `atm1` is newly placed at 44 and
  retained through 85. Its local display list is empty from local frame 31.
- Kon root: 1 parks/stops; 2 plays/fzccXg; 12 action=1; 15 bsd(...,true);
  30 bsw(pn); 67 action=0; 72/75/78/81/85/89 subtract 20 opponent MP;
  102 fzccXg and natural wrap. Other root frames have no script. `atm1` is
  placed at 37, moved without replacement and removed at 65. Sprite 18's
  legacy function definitions have no invoking callback; no nested stop or
  Gaara target-aim hook belongs to Kon.
- The defender's `getHitObj` has no consumed-contact state. Ichigo base Sprite
  638 removes bdmn during 738–740, settles onBeHit at 739, places the beidax
  callback at 740 and the beida receiver at 741. Their first callbacks are 741
  and 742 respectively. Retained sand can hit the replacement receiver again.
- Original `beidax` increments time during playing frames, then resumes when
  time >= tdtime. The legacy versus path counted down only after stop, causing
  four extra held frames. The compiler now retains callback_start_frame and
  source path/hash; the legacy runtime starts motion/timing at that callback.
- Source invariants are tested before Flash validation. The original runtime
  comparison uses isolated copies built by build_ai_reference.py --helper-probe;
  only instrumentation and controlled initial conditions differ from originals.

## Fixes and regressions

Removed HelperRuntime's once-per-attack-instance cache. Both incoming-source
callbacks and legacy helper resolution use the same contact lookup. Legacy
polling waits until the bdmn placement's next frame; source-controlled receivers
already dispatch from the actual callback registry. No per-character hit count,
hit interval, damage multiplier or enlarged box was introduced.

Compiled terminal child stops into helper combat metadata. Rendering and AABB
queries share the child playhead. The old Gaara loop incorrectly revived its
sand during root frames 79–85; the red test reproduced this in both directions.

`helper_repeat_contact_smoke.gd` covers both helpers, both directions, retained
placements/MOVE, receiver replacement, canhit, pause, removal and empty stopped
sand. `kon_helper_smoke.gd` retains six independent drains and wrap assertions;
its setup now waits for the existing introduction before sending summon input.
`test_helper_timing.py` locks original root, child and receiver lifetimes.

## Original-player comparison

Adobe Flash Player Debugger 32.0.0.465 (Rosetta, macOS), locked source hashes and
JPEXS hash are recorded in each capture's build metadata. Source key reads are
validated by the collector. Fixed P1 Naruto O10–14 versus neutral-sample Ichigo,
main floor, P1 X=300; Gaara target X=420, Kon target X=340. Both start with
P1 energy=100. AI refresh is canceled only in the fixture.

- [Gaara r01](helper-woailuo-r01/comparison.json): 165 aligned summon/recovery
  ticks match; eight 30-HP settlements at helper frames 45/49/53/57/61/65/69/73.
  Final HP 760. Root returns from 85 to 1; child stops at 33 without replay.
- [Kon r02](helper-kon-r02/comparison.json): 165 ticks match; five 10-HP
  settlements at 38/42/46/50/54. Final HP 950. Target started at zero MP.
- [Kon high-MP r05](helper-kon-r05/comparison.json): 165 ticks match, including
  five hits and six -20 drains at 72/75/78/81/85/89. Target starts at 200, gains
  5 from hits, and finishes at 85.
- The first
  high-MP attempt (r03) let bisharan=400 trigger source supers; it is retained
  as a fixture failure, not used as a neutral summon baseline. The corrected
  fixture explicitly uses bisharan=NaN to disable its ordered comparisons.

Comparison aligns the first visible helper frame 2, not the boot/Ready standing
phase. Both native post-step and root-observer counters are retained. Root
observation precedes deferred standing-frame hits=0; comparing a post-step
counter to the original root counter invents a one-frame discrepancy. No raw
capture, random tape or expected value was rewritten to suppress that difference.

The additional legacy versus probe confirms the same contact/damage and recovery
frames after the callback timer fix. It still clears hits at the synchronous
standing transition, one root observation earlier than Flash. This existing
legacy scheduling limitation is separate from assistance duration and remains
visible in the retained comparison; full legacy parity is not claimed.

## Validation and remaining limits

Focused native tests and Python source tests pass. The broader combat_smoke
stops at its existing line-289 assertion expecting immediate guard damage;
current source settlement occurs on the later frame script. This assertion is
outside the changed helper/timer path and was not weakened. Native source repeat
contact and Kon scene regressions pass. Headless logs retain the macOS certificate
warning; tests require normal exit and success markers, not just a printed marker.

Native Flash trace validation completed. UI screenshot retrieval timed out, so
no new pixel/visual screenshot comparison is claimed. Web export is a build
check only. M2/M3/M5 remain pending beyond these bounded helper cases.

Final checks: 64 Python tests and six focused native tests passed; verify,
check_handoff and contract checks passed. Release Web export exited 0 and rebuilt
`dist/web/index.html`/PCK. Export retained the sandbox editor-settings save warning;
no new browser playthrough or image comparison was completed.

The Flash log is shared by concurrently running debugger instances. r04 lost its
initial events and was rejected by the collector. r05 was retained continuously
while running and has the complete sequence 1–6765 (including the asynchronous
quit tail). This does not relax capture validation.
