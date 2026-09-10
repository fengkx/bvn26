# Renji Web audiovisual smoke r03

Date: 2026-09-10. URL: `http://127.0.0.1:8060/`. The browser export was served
from `/private/tmp/bvn-renji-web` and exercised in the Codex in-app Chromium
canvas with physical Playwright key codes (`KeyJ`, `KeyA`, `KeyD`, `KeyI`,
`Enter`, `ArrowUp`).

Observed sequence:

1. Entered Vs Com and reached a live battle with Renji as P1. The screenshot
   showed the source-rendered Renji/Naruto sprites, HUD, stage and timer.
2. `KeyA`, `KeyD`, then `KeyJ` moved P1 and produced the ordinary attack/hit
   presentation. A later screenshot showed Renji's attack connecting and the
   opponent health/win counter updated.
3. `Enter` opened the source-derived pause menu (`标题画面`, `出招表`, `返回`);
   the battle frame and HUD remained visible behind it. `Enter` resumed from the
   default `返回` item.
4. `KeyI` reached the authored black-stage special presentation with Renji and
   Naruto sprites isolated against the black background. This confirms the
   production special path is entered by the real browser input; it does not
   establish frame-by-frame original visual parity.
5. `Enter`, `ArrowUp` twice, `Enter` returned to the title menu. Re-entering Vs
   Com and selecting with `KeyD` reached Renji again; the footer read
   `阿散井·恋次` and the large source portrait was visible.

The source comparison anchor is `data/slices/Renji-base.timeline.json` and the
materialized source assets under `godot/generated/fighters/renji/`; the selected
sprite/portrait is visibly present in the Web screenshots. No Flash same-position
screenshot was captured in this slot, so pixel-level source-player comparison is
still pending. Browser audio was not recorded or counted; the source-backed
34-frame sound bake and dynamic envelope evidence remains in the Renji README,
so audio parity is also pending. This is a real-input routing/presentation smoke,
not completion of audiovisual acceptance.
