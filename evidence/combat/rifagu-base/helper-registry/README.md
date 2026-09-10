# Helper root frame registration

This supersedes the rejected global reorder in `../helper-frame-source-first.md`.
The retained original probe records existing instances; it does not add any
MovieClip or change an input tape. Original `game/` and `scripts/` are unchanged.

## Source-first gate

1. All woailuo scripts are in `scripts/fighter/fz/woailuo.json`: root 1 initializes and stops; 2 plays and calls fzccXg; 13 assigns action; 16 calls bsd; 38 calls bsw; 44 shines and the new depth-2 Sprite48 load aims at the opponent X; 85 calls fzccXg. All other root frames have no DoAction. Sprite48 stops at its own frame 33. The helper root wraps to frame 1. Hitsugaya root 818 calls doZhaoHuan and 843 exits to standing; the summon hook is placed at 813. Existing compiled events and exits are unchanged.
2. Helper root instances load after fighter bodies (trace sequences 55 and 80); action-controller instances are subsequently replaced and become newer. Helper activation is goto/play on the retained root, not a new root instance. New depth-2 Sprite48 load stays in its authored frame settlement.
3. Helper completion remains the original root wrap/stop; fighter summon exits via explicit gotoAndStop/play. Neither lifetime changes.
4. Invariants come from `boundary-events.json`: at fight 29, controller/receiver callbacks run before helper frame 16, which enables pause before P2 BODY. At 51, helper frame 38 resumes before P2 BODY but after its controller. At 57, helper frame 44 and its child load settle at the same retained instance position before P2 BODY. The root snapshot ticks are one later than the callback event's fight_tick.
5. `capture.log.gz`, `events.jsonl.gz`, `build.json.gz`, and `instrumentation.diff.gz` retain the 300-tick same-input original capture. Its air-target states match the existing oracle and repaired native output. Full original pixel/audio identity is outside this scheduling fix.

## Repair

Helper root frame settlement now registers with the shared source instance
registry after the loaded fighter bodies. New action clips register later and
therefore run first; the helper then runs before the older BODY callbacks.
The registration is retained across summons and is removed on match teardown.
No new per-character callback order, freeze duration, gravity rule or collider
is introduced. Standalone helper tests may still call enter_frame directly.

## Verification

- Air-target and held-summon each match all 602 actor snapshots after this change.
- Full matrix, cross-mode and lifecycle results are added below after completion.
