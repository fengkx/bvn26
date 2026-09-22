# Lee exact frame-action callback capture preparation

This preparation binds two source frame actions to the existing Lee fixtures:

- `DefineSprite_518/frame_29/DoAction.as` (`瞬步`), `lee-callback-air-actions-r02`,
  P1 小李 / P2 一护, helpers 我爱罗 / 魂.
- `DefineSprite_518/frame_1017/DoAction.as` (`招换`), `lee-callback-summon-r02`,
  same fighters and helpers.

Both builds use `body_boundaries=true`, no frame-order or schedule probe, and
retain the source `frame_action` targets. The native capture command was
attempted with `--lock-timeout 180`; it did not start because the shared
capture lock was busy for the full timeout. No lock was removed and no source
capture is claimed by this preparation. The build and fixture provenance is
copied here so the eventual capture can use these exact inputs.
