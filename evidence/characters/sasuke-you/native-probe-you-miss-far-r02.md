# Sasuke + You helper original-player miss probe r02

This is a source capture record for the explicit far-target miss fixture. It
uses the source helper selector `p1sf=鼬` (`p1_helper=you`) and `p2sf=魂`
(`p2_helper=kon`); no runtime or source inputs were modified.

## Fixture and capture

- Fixture: `/tmp/sasuke-you-miss-far-r01.json`
- Setup: p1 x=300, p2 x=800, both grounded, summon input on p1 ticks 10..13
- Frames after READY: 180
- Fresh build/run: `/private/tmp/bvn-sasuke-you-miss-far-r02`, run ID
  `sasuke-you-miss-far-r02`
- Raw capture: `native-probe-you-miss-far-r02.original.log.gz`
- Collected events: `native-probe-you-miss-far-r02.events.jsonl.gz`
- Summary/build records: `native-probe-you-miss-far-r02.summary.json` and
  `native-probe-you-miss-far-r02.build.json`

The capture completed with 7,140 events, 932 fighter states, 932 helper
states, one `ready`, one `done`, and no post-done events. The build records
`p1sf=鼬`, `p2sf=魂`, `p1_helper=you`, and `p2_helper=kon`.

## Observed miss path

At fight tick 62 the source helper reaches frame 48 with `atm1` present. It
continues through frame 59, reaches frame 60, sets `动作=0` at frame 61, and
continues through frame 75. The frame 76 source action then resets the helper;
the next observed helper frame is 1 at fight tick 90. There is no source frame
92 transition and no source `atm2` window in this capture. This is the expected
no-hit branch for the source callback in
`scripts/fighter/fz/you.json`:

- `frame_48/PlaceObject2_24_3/CLIPACTIONRECORD onClipEvent(enterFrame).as`
  enters `攻击2` only when `atm1.hitTest(opponent.mc.bdmn)` is true.
- `frame_76/DoAction.as` executes `_root.fzccXg(this); gotoAndStop(1);` on
  the no-hit fallthrough.

The capture is source evidence for the miss branch; it is not a Godot parity
claim. The existing r03 probe covered the hit branch (`frame 48 -> 92`) and did
not cover this no-hit branch.
