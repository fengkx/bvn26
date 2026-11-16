# Orihime assist migration

Status: partial implementation, selectable in this branch; full acceptance pending.
Source: `game/fighter/fz/zhiji.swf`, not a standalone fighter.

## Source-first answers

1. `source-audit.json` indexes every root frame (1–91), including empty frames,
   all 15 original script paths/hashes and display changes. There are no nested
   scripts or clip callbacks. Frames 41, 46, 50, 56, 61, 67 and 75 each execute
   `_root.game["p" + sn].mc.hp += 20;`. The target is the summoning player's body,
   not the opponent. There is no cap or conditional in these frame scripts;
   the original capture confirms HP can exceed the initial 1000 maximum.
2. The root display places the first artwork on frame 2 and retains/moves or
   replaces artwork according to the exported timeline. All definitions are
   images, shapes or sounds, not callback-bearing child sprites. Every MOVE,
   placement/removal and sound event is retained in the audit. No guessed
   callback schedule or inherited child state is introduced.
3. Frame 1 parks the root at (-200, -200) and stops. Frame 2 plays and emits
   entry presentation. Frame 14 sets action=1; 16 starts helper super pause;
   31 ends it; 35 requests shine(13443195). Frame 84 sets action=0; frame 91
   emits exit presentation and naturally wraps to the stopped frame 1.
   No synthetic terminal goto is added.
4. Source tests assert the seven independent +20 owner writes and their exact
   paths/hashes, unchanged existing helpers, and rejection of conditional,
   nested, opponent or compound health writes. These are compiler checks,
   not evidence that runtime healing, pause or rollback is correct.
5. An original-player fixture starts P1 at 950 HP, selects Orihime and presses
   summon at ticks 10–12. It is a controlled diagnostic precondition, not an
   untouched full match. Original and native states match; see `comparisons.json` and the raw archive.

## Lifecycle and remaining acceptance

| State | Owner / writes | Reset / preservation |
|---|---|---|
| HP | Caster BODY; seven root frame assignments | Global round setup; no helper-local cap |
| Source action | Helper root; frames 14 and 84 | Source frame-1 initialization and removeFZ rules |
| Presentation pause | Shared bsd/bsw; frames 16/31 | Existing source scheduling must be compared |
| Root playhead | Helper root; starts 2, wraps after 91 | Repeated summon must re-run all seven writes |

The zero-damage gjl packet is preserved as source metadata; there is no placed
attack-region instance or receiver chain to invent. Required next checks include
both owner slots, health boundaries, repeat summon on the same helper instance,
pause/interruption and rollback, aligned visuals/audio and actual Web selection.
All acceptance flags stay false. Local selection and the service catalog now include the same six helpers;
no deployment or full acceptance is claimed.

## Executed checks

Four source/native cases match 2,228 actor rows on 14 exact fields and 2,228
helper rows on six declared fields (frame, X/Y, orientation, action, attacking).
The strict existing comparator uses no tolerances. Raw helper extras remain
uncompared. Three casts reuse the helper instance, heal 21 times and finish at
1020 HP from 600; P2 finishes at 1140 from 1000; 99 energy rejects summoning.
The repeated case moves the opponent between casts.

`before-comparison.json` retains the missing-heal failure; the first difference
is tick 55. Source traces were not changed to make the fix pass. The initial
native runner exit warnings and failed footer import are preserved separately;
final replay, rollback and actual Compatibility-renderer capture logs are clean.
The production rollback check restores after the first heal and reproduces the
entire remaining three-cast state. See `rollback.log`, `selection.png`, and
`healing.png`. Screenshots establish rendering, not Flash pixel equality.

Source/selection tests: 17 passed. Matchmaking tests/typecheck: 32 passed.
Schema examples pass; this is not gameplay certification. Web export and
browser startup are recorded separately when completed.

## Rebuild

Use the standard commands in `docs/OPERATIONS.md` (helper rebuild) with
`zhiji` / `织姬`: export the locked helper SWF with pinned JPEXS 26.2.1,
extract its root timeline, run `build_helper_model.py`, then materialize its
reachable assets. `source-audit.json` retains all frame scripts and placements.
The footer is rasterized from main Sprite/EditText template 670 with the exact
manifest display name; it uses source font glyphs, not a replacement UI font.
The shared menu font was actually regenerated with the complete available
roster. Runtime events are optional; existing helper models do not gain them.

Run `python3 -m unittest tools.tests.test_helper_health_compilation
 tools.tests.test_helper_timing tools.tests.test_selection_registry
 tools.tests.test_selection_portrait_alpha` on one command line, then the
`zhiji_helper_rollback.gd` and `zhiji_visual_capture.gd` Godot runners.

Local standard Web export, packed healing (950 → 1090) and Chromium startup
passed; see `web/` for the PCK/build identity, raw logs and screenshot.
Frozen-snapshot dirty provenance is retained, not relabeled a clean build.
