# Hitsugaya bitmap shape clipping

The reported rectangular ice fragment comes from DefineShape 107, not a map layer. Both native Godot and Web share the same renderer. Bitmap 79 includes the character and a large ice sheet. Shape 80 shows the complete bitmap; shape 107 uses a curved boundary to keep the character while excluding that ice sheet. The previous renderer used only the shape AABB, exposing an approximately 92 by 72 pixel rectangle of bitmap 79 during recovery.

## Source-first answers

- Source: `game/fighter/rifagu.swf`, DefineSprite 638, aerial U (frame 136). Scripts are retained in `scripts/fighter/rifagu.json`. Frame 137 sets khit/jump/action and adds ql; frame 154 calls shine; frame 180 goes to 落2 and plays. Other root frames in this interval have no DoAction. Frame 144's child moves the actor while unpaused. Frame 154's tzatm load initializes played/movspeed; enterFrame checks collision then advances or plays its impact segment. These mechanics are unchanged.
- Frame 154 replaces depth 27 with shape 80 using MOVE; frame 157 replaces it with shape 107 using MOVE and retains the same placement transform. The new tzatm instance at depth 28 is separate from the bitmap boundary and remains unchanged.
- Exit is the authored frame-180 gotoAndStop(落2), followed by play(), not an inferred label end.
- Regression invariant: bitmap 79 pixel (65,68) is opaque but outside shape 107's curved fill boundary; it must be transparent when displaying shape 107. Shape 80 must still display the complete ice sheet. The retained XML is the exact shape 107 tag from the pinned SWF's JPEXS XML export.
- Existing same-input original aerial-U traces are retained in `evidence/combat/rifagu-base/matrix`; this change only changes bitmap fill geometry. The full-match native replay uses the existing rifagu-136-airMagichit-neutral fixture. New original-player pixel parity is not claimed.

## Implementation and boundary

The timeline extractor retains a single closed bitmap contour, flattening quadratic edges with a maximum one-twip chord error. The shared renderer maps source-space polygon vertices back through the bitmap matrix for texture coordinates. Rectangle fast paths are unchanged. Multiple/touching contours remain outside this small compiler's scope. Only shape 107 gains the new field in the current Hitsugaya slice; no map, input, collision, or move-timing rule changed.

## Checks

- `python3 -m unittest discover -s tools/tests`: 91 passed.
- `godot --path godot -s res://tests/bitmap_clip_smoke.gd -- --legacy-aabb`: expected exit 1, visible ice fragment.
- Same pixel regression without the legacy flag: exit 0, `BITMAP_CLIP_SMOKE_OK`.
- Native full-match frame 154 retains the full ice; frame 157 removes the rectangular fragment.

- Browser: Chromium WebGL 2.0, isolated copy of the same project with the regression as its main scene. `web-log.json` contains `BITMAP_CLIP_SMOKE_OK`; `web.png` shows no rectangular ice. The temporary probe hides tzatm to isolate shape 107; the full-match native images retain the projectiles.
- `tools/verify.py`, `tools/check_handoff.py`, `tools/validate_contracts.py`: passed.
- The production Web package is rebuilt from source. No deployment or original-player pixel-equivalence claim is made.
