# Element guard effect source gate

The first difference in `rifagu-136-airMagichit-guard` is fight tick 41.
Original root position is (2, 2) and pause is true; the port stays at (0, 0)
and continues moving. The original raw trace and initial comparison are kept
under the corresponding reference case.

- `scripts/main.json`, `frame_8/DoAction.as#bdfyxg`: grouped cases
  5, 7, 8, 9 and 10 all fall through to `XG_mffyx`. `bdfyxg2` also groups
  1/2 and 3/6. The old regex retained only the first label in each group.
- The shared receiver's `onDefence` invokes that source table. This is not a
  fighter-specific movement rule. The main effect already has imported art.
- `DefineSprite_279_XG_mffyx` frame 2 pauses/shines and its second DoAction
  writes both root axes to 2. Frames 3 through 7 assign authored coordinates;
  frame 8 resumes and resets both axes. Its existing lifetime and callback
  registration stay unchanged. Full frame scripts remain in the locked bundle.
- Every grouped case must resolve to its original clip, including labels with
  no intervening statements. Unsupported nonempty branches fail compilation.
- The fresh original case uses a jump followed by U against a continuously
  guarding opponent. Its 300-tick same-input trace is the expected result;
  both fighter fields and root position are compared without tolerances.

Fix: compile empty case-label fallthroughs and rebuild all current base
combat tables. No runtime character exception, hitbox change or position
adjustment is introduced.
