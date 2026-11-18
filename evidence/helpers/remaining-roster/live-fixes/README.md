# Assist contact and presentation verification

The original desktop Flash projector and Godot ran 26 fixtures with the same starting positions, inputs and observation ticks. The 17 held-guard cases cover every newly ported assist. The other nine cases cover two reverse-side casts, four distances for Temari, two dash timings for Ichigo against Tenten, and Ichigo's own down + attack against guard.

All 7,464 fighter rows and 7,464 helper rows matched on the 14 fighter fields and six helper fields used by the roster comparison. Every received attack matched on tick, defender and branch. There were 49 blocks, 10 guard breaks and 25 ordinary hits. The two empty contact sequences also matched.

| Input | Flash and Godot result |
| --- | --- |
| Hold guard against Minato | Block on tick 48, guard break on tick 76 |
| Hold guard against Nemu | Blocks on ticks 52 and 59, guard break on tick 77 |
| Ichigo uses down + attack against guard | Guard break on tick 30, defender finishes at 920 HP |
| Ichigo dashes on tick 54 against Tenten | First hit on tick 67, three received attacks, 880 HP |
| Ichigo presses dash on tick 66 during hitstun | Seven received attacks, 800 HP |
| Temari at x=300, defender at x=555.75 | One hit, 975 HP |
| Same cast, defender at x=555.80 | Zero hits, 1,000 HP |

Packet ticks refer to the most recent Flash root observation. The next observation can show the result of the packet. Each case in [checks.json](checks.json) includes the inputs, positions, per-slot health and ordered packets. [The compressed traces](traces.json.gz) retain the Flash state, attack and hit-test records and the Godot state and receiver diagnostics for independent inspection. The browser results in the same JSON come from a release-format local WebGL build. A physical-key event sent through Chromium activated each assist. Visible sprites, active duration, final HP and return to idle matched the previous browser run for all 17.

## Visual comparisons

Each image shows the Flash stage, the previous Godot render, and an independently replayed corrected Godot render. Flash stage capture applies the root matrix so both renderers include the same impact shake. The HUD now has a stage-sized draw area. Sprite 1991 positions both player markers using the camera target before interpolation. Mirrored effects use the signed X axis from Flash. For the orientation comparisons, Godot replays the recorded AVM integer random draws. Live play draws new angles.

| Frame | Difference verified |
| --- | --- |
| [Yachiru 71](baqianliu-71.jpg) and [Tsunade 65](gangshou-65.jpg) | Health bars stay visible during impact shake |
| [Tsunade 96](gangshou-96.jpg) and [Grimmjow 132](grimmjow-132.jpg) | Both player markers appear at the Flash stage positions |
| [Shishio 82](shishio-82.jpg) and [Suigetsu 63](shuiyue-63.jpg) | Explosion and hit splash use the observed rotation and reflection |

The frames still show renderer-level pixel differences. The round timer also reflects elapsed time during projector capture. The contact comparison uses fight ticks and excludes the HUD timer.
