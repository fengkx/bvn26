# Sakura window 13 last eligible input

Run ID: `moves-sakura-window-13-last-input-r01`.

The source cancel window is the closed frame interval 393–402 for `砍技2 → 空中必杀`. Since the source observes the input in the following callback, the final tested eligible input is delivered at fight tick 46 after observing source frame 401; the destination is first observed at tick 47 on source frame 646. The old after-frame-402 case remains the too-late side. Fixture input, original capture, and source-window metadata are retained alongside this note.

The original capture completed 300 post-ready frames with 11,477 events and source target observed. Native GameWorld fighter and helper comparisons each match all 602 rows exactly (`comparison/sakura-window13-last-input-r01-fighter.json` and `...-helper.json`). The boundary summary is `comparison/sakura-window13-last-input-r01-boundary.json`.

The original build used `presentation_probe=false`; it captured no source root-position events. Therefore this case makes no root-position parity claim. The evidence is limited to the source input timing, transition, and compared fighter/helper fields.
