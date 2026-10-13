# Source-exact projectile contact callbacks

Base: `46567086` (`origin/master`, including Neji PR #7). The original SWFs,
script bundles, saved inputs and Flash expectations are unchanged.

## Causes and changes

Both failures came from using the receiver's settled-hit cache as the result of
an independently scheduled child ClipAction `hitTest`. The child must evaluate
its current source bounds and targets on every callback, including when the
receiver's `bdmn` is absent during hit reaction. Its source `played` guard owns
one-shot movement/animation changes; receiver history does not.

- **Kakashi ground ranged:** overlapping placements reuse attack names. Cached
  contact prematurely takes the new child's collision branch, advancing its
  stop/rename sequence at the wrong time. P2 diverged at tick 33; tick 34 had
  4 hits / 880 HP instead of 3 / 910. There were 262 different states. The
  fourth source hit belongs later, so comparing only final damage missed this.
- **Sakura 招1:** cached receiver contact prematurely advances the projectile's
  hit animation. It reaches its terminal child frame too early; the source
  projectile is still at frame 6 in the tick-53 receiver callback. Native missed
  the fourth settlement at tick 55 and the pause at 56: 492 different states.
  A fresh, read-only Flash hit-receive capture reproduced all 602 saved states.

`godot/fighter_runtime.gd` now uses compiled collision queries before the legacy
fallback. Empty query lists still mean movement-only callbacks (the Neji rule).
`tools/importer/build_combat_model.py` also corrects an optional-regex-group bug:
a bare `hitTest(...)` has receiver `self`, not the empty-name child. Explicit
named receivers such as `hitmc.hitTest(...)` remain named receivers.

Kakashi/Sakura projectile data and controller metadata are refreshed with their
source load locals, guarded writes and queries. The remaining stale implicit
receivers in Byakuya, MinRen, RiFaGu and YiHu generated data are refreshed from
their recorded source paths. No character-specific runtime branch is added.
The online compatibility fingerprints are regenerated for the changed behavior.

See [the five-question source gate](source-first.md), [baseline differences](baseline.json)
and [machine-readable regression results](regressions.json).

## Validation scope and results

- Both target cases: **602/602 states each, zero differences**, using the existing
  comparator's exact equality on every row and all 14 fighter fields.
- The 53 saved Neji premerge comparisons now all match (previously 51 matched,
  2 historical differences). Five additional saved cases cover Sasuke/Renji
  overlap, Rukia defence and Lee's clean kill/dead timer branches.
- Combined corpus: **58/58 cases, 40,476/40,476 states, zero differences**,
  covering **13 primary fighter roles**. Renji appears only as the opponent in
  two Sasuke overlap cases; this is not independent acceptance of all 14 roles. The 19 cases affected by the remaining
  implicit-receiver metadata refresh are rerun after that refresh.
- Roster rollback: **14 fighters × 8 checkpoints = 112 exact restores**, plus
  dedicated Neji, Chad and Yin rollback checks and round-reset smoke.
  The old roster test's final printed `fighters=11` is stale; the count here
  comes from its 14 successful per-fighter case markers.
- **13 Godot checks** pass: projectile driver, instance locals, Kakashi semantics,
  player controller/visual, combat, source hitTest, round reset, three dedicated
  rollback tests, roster rollback, and six contact-history casts across both
  directions. The combat smoke now creates a real target collision instead of
  treating `mark_attack_hit` as an invented source collision.
- Compiler/source tests: **48 tests** (47 existing/new tests in the initial run,
  then the contact module's 3 tests after adding the all-artifacts source check).
  Shared receive-chain gate: **5 tests**, covering 35 fighters and 26 helpers.
  Online manifest: **7 tests**.

This is the saved regression corpus above, not acceptance of every archived
experiment, unsaved move, AI path, or visual/audio/Web behavior. M2 milestones
remain pending. No baseline output or comparison tolerance was edited.

## Reproduce

Use an imported Godot project and Python 3.10+; no Flash recapture or login is
needed to replay the saved corpus:

```sh
python3 tools/test_projectile_contact_references.py --godot /path/to/Godot --output /tmp/bvn-contact-replay
```

Add `--case kakashi-ground-ranged-contact-r01 --case sakura-415-magichit1-neutral`
for only the two target cases. The runner verifies saved source/fixture hashes,
requires successful Godot execution, and checks every observation without a
tolerance. This entry point was itself exercised on both targets (1,204 states).
The report records portable source paths, copied fixtures, and compressed native
observations; source traces formerly only in `/tmp` are retained losslessly.

Focused commands:

```sh
python3 -m unittest tools.tests.test_projectile_contacts tools.tests.test_source_inventory tools.tests.test_kakashi_compilers tools.tests.test_kakashi_source_audit tools.tests.test_neji_import
Godot --headless --path godot -s res://tests/projectile_contact_history_smoke.gd
Godot --headless --path godot -s res://tests/combat_smoke.gd
Godot --headless --path godot -s res://tests/rollback_roster_smoke.gd
python3 tools/verify.py
python3 tools/check_handoff.py
python3 tools/build_online_manifest.py --check
```

Fresh Sakura capture provenance, instrumentation diff, tapes and compressed
original events are in `fresh-sakura/`. Its observation-only instrumentation did
not change any of the 602 saved fighter states. No credentials or login was used.


## PR #10 review follow-up

The earlier receiver-only refresh missed Naruto/Hitsugaya load locals and the
Naruto/Hitsugaya/Ichigo guarded contact writes. Recompile all five affected
projectiles with the existing compiler, synchronizing `data/actions`, runtime
combat data and controller hooks. Byakuya's AI hook also now retains its source
load locals. Source-driven guards set played=1 and movspeed=0 together with the
child goto; contact loss cannot restart flight. The all-artifact Python check
now verifies every compiled motion/initialization field, not only query lists.
Kakashi action data now preserves the same 12 motion windows as runtime combat.

Fresh Flash Debugger comparisons cover Naruto neutral ranged and Hitsugaya
**guarded** air ranged: **22/22 + 27/27 child states**, with **18 post-contact
observations each**, and **1,204/1,204 fighter states**. The ordinary Hitsugaya
neutral/air-target fixtures deal damage without taking the child's hitTest
branch, so they are insufficient to prove contact stopping. The new fixture
retains the saved guard case's inputs and setup and adds read-only observation.

The review rerun has **23/23 affected/target cases, 13,846/13,846 fighter states,
zero differences**, including guard, attack/trade, air target, mirror, wall and
dash cases. This is distinct from the historical 58-case corpus above.
**50 Python tests** and **3 Godot checks** pass (contact-history: six casts,
instance locals, combat). The isolated combat fixture now executes source load
before child callbacks, as the production controller already does. These checks
retain existing Godot shutdown resource-leak diagnostics; no SCRIPT ERROR or
assertion failure remains. Production runtime, locked inputs and tolerances are
unchanged. Full milestones stay pending.

See [review results](review.json) and [child-state evidence](projectile-states/README.md).
Replay the two new captures, including both fighter and child state checks:

```sh
python3 tools/test_projectile_contact_references.py --projectile-states --godot /path/to/Godot --output /tmp/bvn-projectile-states
```


## PR #10 re-review: frame-1 initialization

The preceding follow-up missed Ichigo's frame-1 declarations: legacy
`initial_speed`/`initial_played` did not seed the runtime's source-local map.
The shared compiler now emits `initial_variables` for this pattern, and all
three Ichigo action/combat projectiles plus player/AI hooks are refreshed.
Naruto, Hitsugaya and Byakuya lose only redundant `initial_played` fields.
Runtime judgement and scheduling are unchanged.

Fresh Ichigo guard capture matches **21/21 child states**, including **12
post-contact states**, and **602/602 fighter states**. Alongside rerun Naruto
and Hitsugaya captures, the contact total is **70/70 child states and 1,806/1,806
fighter states**. The preliminary Ichigo neutral capture has no value mismatch
but does not exercise child contact; it is retained separately and excluded.

Focused saved replays pass **22/22 cases, 13,604/13,604 fighter states**, including
all three Ichigo attacks, Naruto ranged, Hitsugaya/Byakuya guard and trade cases,
and Chad/Gin/Neji interrupt cases. **17 distinct compiler/projectile Python tests,
7 online-manifest tests and 21 contact-history casts pass**; all **9** child
X/frame/speed mutation negatives are rejected. Package integrity, handoff,
online fingerprints and whitespace checks pass. This supersedes the preceding
claim that Ichigo initialization was complete; historical counts remain separate.
See [re-review results](rereview.json) and [source gate](source-first.md).
