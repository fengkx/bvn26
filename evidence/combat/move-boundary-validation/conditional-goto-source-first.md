# Conditional frame goto — source-first record

1. Naruto Sprite 764 frame 538 contains exactly one branch: when the opponent's
   HP is greater than zero and action is -1, execute `gotoAndStop("必杀1"); play();`.
   This tests the opponent's current state, not an invented per-attack hit flag.
2. The source frame changes no PlaceObject/MOVE itself. A successful jump replaces
   the timeline's display list through the existing source host; no controller
   instance may be manually retained or synthesized after that jump.
3. On false, the playhead continues. Frame 542 unconditionally jumps to `必杀0`.
   On true, it enters `必杀1` at 543. Its eventual fallthrough remains authored.
4. Conditions must be evaluated at frame-script dispatch, before the deferred
   target script. Zero/negative HP or any action other than -1 must not take the
   branch. The original two statements remain ordered in a compiled block.
5. Original `minren-504-bisha-neutral`: at tick 44 the opponent has HP=990 and
   action=-1; tick 45 enters 543. The prior port stays at 538 and later enters
   the miss continuation. The original guard traces supply the non-hit branch
   regression. Keep the red trace and compare all 602 states after repair.

Root cause: the frame-call extractor admitted unconditional goto/play but silently
skipped indented statements inside this branch. The old hand-written move path
had a separate check; shared source execution exposed the compiler omission.
The repair belongs to source frame compilation, not a Naruto runtime exception.
