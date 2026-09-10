# Helper ordering: acceptance failure and rejected experiment

Status: **unaccepted**. All experimental helper scheduling changes were reverted.
The final runtime matches checks/gameplay-runtime-hashes.json.

The original summon-air-target case pauses P2 at tick 30/frame 63/Y=-32;
the retained runtime instead reaches Y=-25 and sets touch/touchFloor first.
The original held-summon case also differs at tick 115 (P2 frame 2 versus 1).
Source woailuo root frame 16 calls `_root.bsd(pn,"XG_fzbs",true)`, frame 38
calls bsw, and frame 44 places a child with a distinct onClipEvent(load) aim
write. Hitsugaya Sprite 638 summon places beida at 813, calls doZhaoHuan at
818 and exits via gotoAndStop(stand)/play at 843.

An experiment moved helper root frame settlement before fighter callbacks,
while leaving child load aiming after them. It matched all 602 actor and 301
root observations in the airborne case, but the wider matrix rejected it:
guard, repeated dash and held summon responded earlier than the original.
Moving load aiming earlier too additionally caused contact at tick 58 instead
of 59. Neither variant is a valid shared scheduling repair.

The remaining source-first gap is the exact instance/frame callback order at
these pause/resume and replacement boundaries. A dedicated original-player
trace must instrument helper root frame scripts, new/retained fighter controller
callbacks and helper load callbacks together. Aggregate root snapshots identify
the failure but do not establish a global reorder rule. No gravity, collision,
freeze duration, fixture or comparator threshold was changed to hide it.

helper-frame-order/ retains the original, original runtime failure, rejected
candidate traces and cross-case rejection summary. Its after.json.gz is an
experimental case-level green, **not** the final runtime or accepted repair.
