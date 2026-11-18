# Tsuchikage assist

Partial implementation. Full acceptance remains pending.

The original catalog maps 土影 to fighter/fz/tuyin.swf. Its root has 66 frames.
Frame 1 parks and stops the helper. Frame 2 starts entry presentation, frame 13
sets action, frame 16 enters the helper super, frame 30 releases it, frame 36
requests shine, frame 62 clears action and frame 66 emits the exit effect.
Playback naturally wraps to the stopped frame 1.

The source timeline places atm1 on frames 33–36, atm2 on 37–48 and atm3 on
51–53. Attack packets specify 20, 50 and 100 damage, with the final packet
using the launch reaction. The exported timeline retains every MOVE and
placement lifetime. There are no placed clip callbacks in this helper.
The root entry and existing shared helper lifecycle handle repeat summons.

The locked source scripts and generated timeline supply the frame and
placement evidence. Original-player diagnostic traces and identical Godot
fixtures are compared separately. Final results are recorded below.

Original captures settle damage at fight ticks 48, 52, 56, 60 and 66, leaving the target at 730 HP. The mirrored case reproduces these hits. A second cast at tick 130 misses the displaced opponent.

Both diagnostic fixtures match all 14 actor fields across 804 rows and the six declared helper fields across 804 rows. Raw traces, probe metadata and comparison reports accompany each fixture. Pixel/audio alignment, rollback and browser gameplay remain pending. Godot startup logged a macOS system CA lookup error, and both replay runners completed.
