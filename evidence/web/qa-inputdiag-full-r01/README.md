# Full-roster QA input probe r01

Temporary export with the complete existing nine fighters and four helpers plus the two QA candidates. The source selection grid is unchanged.

- URL: `http://127.0.0.1:8783/`
- PCK SHA256: `7c3a4c281b7322e692f7556f586d1a86fee285fef87a41c6eeabcb57247d815d`
- Fighters: existing nine plus 白哉/byakuya and 小李/lee.
- Helpers: existing four (鼬, 魂, 我爱罗, 松本).
- QA probe is temporary and does not change production control logic.

## page32 full UI run

- Page: Chrome DevTools page32, isolated QA context `bvn-full-r02`.
- Mode and selection: mode3 (Vs Human); P1 白哉, P2 小李; helper phase selected P1 魂 and P2 我爱罗; map confirmed into the battle scene.
- The full original selection grid remained present while the two candidates were temporarily marked available. Selection was performed with held canvas keyboard events and screenshots after incremental moves; no direct selection call or forced battle entry was used.
- PCK: `7c3a4c281b7322e692f7556f586d1a86fee285fef87a41c6eeabcb57247d815d`.
- Raw DevTools console response: `raw/page32-console-tool-output.json` (SHA256 `dbf8d030bc78a1cdb462d168fd85b4f68162e1d70f855a0d5d4ecd6e0e80cef2`). This is the direct `list_console_messages` response, not a hand-written excerpt; `msgid` is the DevTools message id.
- The response includes the actual role transition at messages 94-95 (`fighter=白哉`, `fighter=小李`), mode3 probe records, physical/logical held input records, and combat settlements. The first in-battle J hold produced `fighter=小李`, health 1000→970→940; the P2 Numpad1 hold produced `fighter=白哉`, health 1000→980→960. A D hold produced `p1.right=true` in the probe.
- The initial long action sequence used the 37-second round timer and reached timeout before its Enter attempt; that portion is evidence for selection, role loading, input delivery, movement and attack settlement only.
- A short follow-up on the same page caught the next round before timeout: Enter opened the visible pause menu, and a second Enter removed it while the match continued. The follow-up direct console response is `raw/page32-console-after-pause.json` (SHA256 `76a23912c60783568cf7a31602c9ddd07d529135ff8e1bc902708ac3b73b10ff`). The probe's sampled records remain `paused:false` because the pause menu's display interval was shorter than the probe sampling boundary; the visible pause-menu screenshot is the evidence for the UI transition. This closes pause/resume only, not return-to-selection.
- The screenshot tool refused saving to both the repository evidence directory and `/private/tmp`; inline screenshots were inspected during the run. No screenshot file is claimed here.
- Console warnings retained verbatim: WebGL `INVALID_OPERATION` for `bindBuffer` and `bufferSubData`; no Godot parse or script error appeared.
