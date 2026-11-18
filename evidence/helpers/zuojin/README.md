# Sai assist

The original catalog maps 佐井 to `fighter/fz/zuojin.swf`. The root has 71 frames.
Frame 1 parks the helper and stops. Summoning starts at frame 2. The root sets
action at 12, enters the helper super at 15, releases it at 31, requests the
black flash at 33, clears action at 54 and emits its exit effect at 71 before
wrapping. The compiled combat model records the source path and hash for each
of the 12 scripts. The timeline records every placement, MOVE and removal.

Root frame 32 places sprite 27 at depth 2 under the name abcd. Its load handler
sets the local X from the opponent's position and the helper's facing. Child
frame 5 assigns the name atm1, frame 8 restores abcd and frame 23 stops.
The original helper_clip_state trace sees atm1 at child frames 5, 6 and 7
(root frames 36–38). The attack uses the bounds of the live placement.
The original player and Godot both settle 200 damage on the following sample.

## Replays

The fixtures use diagnostic input injection with Ichigo and Naruto on the
original stage. Run the Godot move_case_reference runner with either fixture.
Compressed original events, native states, helper projections and probe build
metadata accompany each case. comparison.json contains the strict comparisons.
The collector retained the post-done tail separately during collection. Only
the requested interval enters the comparisons.

| Fixture | Expected HP transitions | Actor rows | Helper rows |
| --- | --- | ---: | ---: |
| summon | P2 reaches 800 on tick 51 | 272 | 272 |
| p2-repeat | P1 reaches 800 on tick 51 and 600 on tick 162 | 462 | 462 |

All 14 actor fields and six helper fields match at every sample. The original
events also retain clip state for independent inspection. Headless Godot
logged a macOS system CA lookup error during startup. Both final replays
completed. Pixel and audio alignment, rollback and browser gameplay remain
open.

The local Web preview loads the packed Sai data and footer and boots in Chromium. See web-preview.json for the tested PCK hash. Browser gameplay and final online-room interoperability remain unverified.
