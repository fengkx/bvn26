# Shared coordinate storage — source-first record

This is a source-backed runtime change prompted by the `minren-472-magichit3-neutral`
original/native difference. It does not establish complete move or geometry parity.

1. **Scripts:** Naruto Sprite 764 frame 478 places a callback that adds/subtracts
   `speed * 1.8` to wrapper X and subtracts `speed * 2.4` from wrapper Y when
   root pause is false. Frame 485 replaces it with horizontal `speed * 1.7`.
   BODY pressure also writes opponent X; therefore a per-move offset is incorrect.
2. **Placement/MOVE:** the callbacks are authored PlaceObject2 instances at depth
   36, with first enterFrame after placement. The existing source instance registry
   owns their lifetime; this change does not synthesize additional callbacks or MOVE.
3. **Exit:** frame 491 explicitly executes `gotoAndStop("落"); play();`.
   Label end 503 must not replace that jump or manufacture a stand transition.
4. **Invariant:** native FP32 setters truncate toward zero to integer twips after
   each assignment, using double arithmetic before conversion. The isolated AS2
   probe records 15 direct assignments and 40 repeated signed writes. For example,
   300 + 14.4 becomes 314.4; the next write becomes 328.75, not 328.8. Negative
   values truncate toward zero, not floor. Rendering vectors cannot retain the
   canonical double-valued source position.
5. **Original same input:** a fresh PvP fight, X=300/350, energy=300; P1 up+ranged
   held on observations 10–12. At tick 18 source X=314.4/Y=-44.2; at tick 19
   X=328.75/Y=-63.4. The unmodified native trace first differs at tick 18 and
   has 564 differing states. Preserve that red trace. Re-run after changing the
   shared adapters; no tolerance or oracle edits are permitted.

The scalar coordinate rule does not certify float32 collision rectangles,
projectile-local matrices, root camera geometry, or all other setter types.
