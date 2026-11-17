# Web keyboard verification

Local release build `2cda604aa53d1303bf33f429e03bea31d36b9a80ffee163374916a35f209bcf1`,
PCK SHA-256 `e0b77f7e1c5d11922bbe534e6101dd96aa03568d0f495f8312283e6dc7b09fa0`.
The sidecar records the working-tree and generated import provenance. Import,
export, compatibility manifest, lobby UI and packaged metadata checks passed.
The Vercel preview required login, so these are local Web captures, not evidence
of a production deployment.

Actual browser keyboard actions navigated Training, selected Ichigo Bankai and
then Sage Naruto, confirmed helpers/stage and executed `S+I`:

- `yihu-2-down-i.jpg`: the purple crescent travels across the stage without its
  former solid bounds rectangle. Two casts were observed.
- `minrenx-down-i-start.jpg`: the opening clone/sphere sequence.
- `minrenx-down-i-wind.jpg`: after moving close to the opponent, the hit sequence
  shows the authored wind curves without the former white/cyan rectangle.

The isolated native same-input comparisons remain the combat evidence; these
manual Web runs verify the exported rendering and real keyboard flow.

`browser-errors.json` retains two Godot viewport lifecycle errors
(`is_input_handled` / `push_input`, `!is_inside_tree()`). The browser remained
playable, but this is not a zero-error Web acceptance. Their trigger was not
isolated during this visual check; no speculative lifecycle guard was added.
