# Naruto One Tail upper special solid geometry

## Source-first questions

1. `scripts/fighter/minren.json`, BODY `DefineSprite_1293`: upper special enters
   frame 560, falls into the air-special label at 561. `source.json` retains every
   timeline frame and all scripts through frame 649, including empty frames.
   Frame 563 invokes `bsd/showFace`; frame 579 invokes `bsw`.
2. Shape 948 is newly placed at depth 30 in frame 583, then MOVE updates its
   scale/translation and alpha. Its XML (`shape948.xml`) has eight quadratic
   curves with an active red fill and a red round 20-twip stroke. The shape
   bounds include the stroke; they are not the painted contour.
3. Shape removal and BODY exits remain the retained timeline/scripts; this
   change only compiles paint geometry and does not change playback or input.
4. The invariant is a curved fill plus its authored stroke, not an AABB. Neither
   sprite ID nor character identity belongs in the renderer's geometry decision.
5. Same-input Flash and Godot bitmap samples at fight tick 40 reproduce a circle
   in Flash and a rectangle in Godot. Flash capture timed out during tick 93;
   complete bitmap frames 0–92 remain usable evidence, not a completed 100-frame
   capture. The original logs and comparison samples are currently in
   `/private/tmp/bvn-red-block` pending final archive.

Visual defect confirmed. Corrected render comparison and browser verification
are pending; this is not a full audiovisual parity certification.

## Measured repair

The native macOS renderer reproduces the source circular fill and round stroke
at fight tick 40 after the repair; the pre-repair image shows the same rectangle
as the user's report. The production Web build was also exercised in the in-app
browser: Training → Naruto One Tail → upper special reproduces the rectangle.
The repaired Web build is pending verification.

The source RLE excerpts retain all non-bitmap events and complete bitmaps at
ticks 40 and 50; provenance records the full unmodified raw capture hash.
`before-040.png`, `after-040.png`, and `original-frames-040.png` are corresponding
samples. Pixel comparisons are diagnostic, not an exact-pixel pass: color,
HUD timing and other raster differences remain. No tolerance was relaxed.

Thirteen source-geometry tests and eleven selectable-form/package tests pass.
Shared PvP and training references each match 602 actor states.
