# Roster visual regression fixtures

The comparison images show Flash Player, Godot before the fix, and Godot after the fix, from left to right. Each panel contains the same 600 × 400 fight observation. The three newly captured fixtures used the HIGH render surface. The Bankai banner replays the archived native-stage fixture at 600 × 400. The source game files and original inputs are identified in each fixture's build metadata.

| Fixture | Source behavior and reproduced result |
| --- | --- |
| [Kakashi U followed by Tsuchikage](kakashi/comparison.webp) | Kakashi sprite 710 places sprite 244 at frames 425 and 437 as zh1atm, and at 431 and 443 as zh12atm. The older instance remains alive when its successor is placed. Its sprite frame 3 renames it to abcd. Each ClipAction retains its own local position, playhead and played flag. The corrected U contacts occur at ticks 86, 93, 100 and 107, followed by four assist contacts at 236, 240, 244 and 249. At tick 250 P2 is at x=479 in both engines. |
| [Jugo's super](juggo/comparison.webp) | Sprite 517 selects the caster with the opponent slot number on frame 918 and restores all-player focus on frame 1000. The same source statements occur in Lee sprite 518. On fight tick 240 the best integer translation of the background patch (x=49..210, y=86..229) changed from (17, 4) to (0, 0). |
| [Rukia with Kon](rukia/comparison.webp) | Main sprite 256, XG_qdj frame 1, draws Math.random four times for the two position writes. The fight fixture replays this stream as well as the independent rotation stream. The centroid of orange pixels in the tick 250 impact region (x=301..403, y=235..354, R>245, 70<G<200, B<50) is (361.52, 300.05) in Flash, (355.38, 319.34) in the previous unsynchronized capture and (362.04, 300.21) in the corrected replay. |
| [Bankai Ichigo’s super banner](banner.webp) | The background timeline places the four-frame speed lines at depth 1 and main shape 1516 at depth 3. The latter contains a padded linear gradient with alpha stops 255, 0 and 255. Restoring its authored contour and matrix reduces the mean absolute RGB error over x=180..564, y=64..184 at tick 145 from 18.68 to 0.53 (0–255 scale). |
| [Kenshin with Fourth Hokage](kenshin/case.json) | The assist inherits the caster's source Y coordinate of -103.65. Compare the exact twip coordinate throughout the summon, including the first active observation at tick 201. |

Each case retains the original state rows and the capture metadata. For example, from the repository root:

```sh
fixture=evidence/combat/roster-visual-fixes/kakashi
godot --headless --path godot -s res://tests/move_case_reference.gd -- "$PWD/$fixture/case.json" /tmp/kakashi-state.json
python3 tools/probes/compare_mode_reference.py "$fixture/events.jsonl.gz" /tmp/kakashi-state.json --output /tmp/kakashi-comparison.json
```

When collecting another bitmap move capture, `tools/probes/collect_ai_reference.py` writes `replay-case.json` with the two recorded random streams. The move runner checks consumption through the end of the fight window.

The 120 original-reference replays cover 40 fighters and forms. All 60,000 fighter observations matched across the move, guard-break and ultimate cases. The 40 summon replays cover all 26 assists. All 23,680 assist observations and both players' sequences of received hit events matched.
