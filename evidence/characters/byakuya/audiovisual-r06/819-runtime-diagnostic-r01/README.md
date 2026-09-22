# Byakuya 819 helper/effect runtime diagnostic r01

This is an analysis-only same-input diagnostic. The dispatch-phase fix described below was experimental and has been reverted; production runtime remains at the pre-experiment hash.

A fresh native Flash capture with a read-only root callback observer was built from the explicit Byakuya 814 summon fixture. At source display tick 472/fight tick 16 the observer records `root.game.p1.mc` frame 819 and `root.game.p1fz` frame 2, while `root.game.layer_effect.xgmc0` is still undefined. The next source callback, display tick 473/fight tick 17, first observes `xgmc0` at local frame 2. The older r29 post-freeze snapshot also observes frame 2, but cannot establish the creation callback phase by itself.

The helper frame-2 script in `scripts/fighter/fz/kon.json` calls `play(); _root.fzccXg(this)`. `fzccXg` attaches `XG_fzcc` under `root.game.layer_effect` as `xgmc0`. The source effect is `DefineSprite_379_XG_fzcc`, timeline frame 2 character 362, with matrix translation `(-651,-1190)` twips and unit scale. The helper is `root.game.p1fz`, source character 2, local frame 2. These values come from locked source traces and exported timelines; they are not inferred from screenshots.

The reverted Godot probe currently observes an effect at local frame 1 in the same p1 frame-819/helper-frame-2 phase, then frame 2 on the next callback. This is a concrete one-callback phase difference. It is not yet a production fix: the source evidence now identifies a one-callback early placement; no shared runtime change was retained in this task.

Fresh source capture command and persisted evidence are in `evidence/characters/byakuya/audiovisual-r06/819-effect-phase-source-r04/`.

## SOURCE_FIRST

1. **每帧脚本：** `scripts/fighter/fz/kon.json` frame 2 executes `play(); _root.fzccXg(this)`. `fzccXg` calls `addChildXG`, which creates `root.game.layer_effect.xgmc0`.
2. **PlaceObject/MOVE：** `DefineSprite_379_XG_fzcc` is attached under `layer_effect`; its frame 2 display list uses character 362 with matrix `(-651,-1190)` twips and unit scale. The helper supplies x/y/xscale to the new outer clip.
3. **离开标签：** the helper remains on its authored timeline; the effect has its own three-frame timeline and is removed by its authored end/unload path. No role-specific frame skip is assumed.
4. **原版不变量：** source helper spawn is logged at display 471/fight 15. The following root callback at display 472/fight 16 observes helper frame 2 but no `xgmc0`; display 473/fight 17 first observes effect frame 2. A newly placed effect is therefore not visible to the same root observer callback that observes the helper's frame-2 transition.
5. **同输入对照：** the current Godot root observer sees effect frame 2 while fighter frame 819/helper frame 2, one callback earlier than the fresh native source capture. This is the accepted diagnostic first difference; the experimental dispatch fix remains reverted pending a shared generic fix and regression.
