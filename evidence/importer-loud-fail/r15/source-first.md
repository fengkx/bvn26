# Source-first: Yihu replacement and nested stage actions

1. Frame scripts: base638/frame1052 invokes original wankai; wrapper nextFrame
   replaces it with1180. Its doWanKai target is871, observed872 next display.
   Body1180/frame1036 replaces with1672, observed1004. Original wankai/doWanKai,
   load declarations, wrapper transfer, slot keys, root timers and live references
   reuse the already source-compiled form helpers (r07–r13). No Godot node identity
   is used as AVM1 reference equivalence.
2. Placements: body1180/frame871 newly places anonymous sprite1027; it persists
   at872. Its16-frame nested timeline advances independently of the body.
   The new body and newly placed target children advance in the replacement
   display pass: at body872 the nested clip is already on2. This is why native
   root Y is12 at body872,17 at873, and repeats -5 at887. Third-form nested
   sprite1652 has the same source scripts. The base's637 is also compiled.
3. Exits: the16-frame stage clip has no terminal stop/goto, so it loops while
   placed and retires on removal/replacement. Frames1/3/5/7/9/11/13/15 apply
   -5/+5/-4/+4/-3/+3/-2/+2;15 calls _root.shine(). Generic stop/play remains
   owned by the source-pinned VisualPlayhead controls. Unsupported lines in a
   stage-writing clip now hard-error with SWF/path/line.
4. Invariants: native root17 produces exactly the23 recorded root positions and
   body frames, HP/energy transfer671/234 and undefined replacement gap.
   Generic stage actions compile for all matching retained symbols (inventory
   lists them); they are not a character-name offset. Repeated render and
   checkpoint refresh cannot execute frame scripts. Full rollback restores the
   Control root position as well as its shared form-root dictionary.
5. Same input: fresh Debugger32 root-observer capture invokes original wankai
   under paused movement, preserving child definitions and non-action tags.
   Godot uses production profiles and compares the23 samples without tolerance.
   The second edge uses the existing r13 native bound. Natural attack+jump checks
   cover all seven admitted graphs. Full transformed combat and component image
   parity remain separate open work; this evidence does not claim them.

No new stability deviation, allowlist or pixel tolerance. The existing documented
online simulation-clock policy is unchanged.
