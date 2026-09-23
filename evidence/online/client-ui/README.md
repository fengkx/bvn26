# Online client UI browser evidence

2026-09-23. This records the production Web export's main-menu path into the
online room home. It contains no room IDs, invitation codes, credentials, HTTP
bodies, WebRTC descriptions or ICE candidates.

## Browser path

- The isolated Chrome test profile opened `http://127.0.0.1:8000/`; the room
  service endpoint shown by the UI was the explicit development address
  `http://127.0.0.1:8787`.
- The page was initially backgrounded (`visibilityState=hidden`). For each
  short test input, the driver temporarily enabled CDP focus emulation, called
  `canvas.focus()`, and restored focus emulation in `finally`. No OS lock state
  or user browser page was changed.
- After a clean page reload removed an earlier temporary probe listener, trusted
  `KeyS` down/up events reached the game canvas. The observed title-menu hints
  advanced through `格斗练习`, `游戏设置|按键设置`, then
  `联机对战: 创建或加入好友房间`. A trusted `KeyJ` down/up opened the online
  room home.
- The room home rendered the experiment label, local-test/network-parameter
  note, development endpoint, nickname and room-code fields, and the
  `创建好友房间`, `加入房间`, and `关闭` actions. The title-menu and room-home
  static Chinese text had no missing glyphs in the browser review.
- Navigation into the room home made no HTTP request. No room was created or
  joined in this browser run. A subsequent room-creation interaction was
  rejected by automatic review because it would write matchmaking state and
  explicit user authorization was still pending. Nothing attempted a second
  route to create the room.

The diagnostic screenshot was inspected in memory and was not retained as a
repository image. This evidence establishes the browser menu and room-home UI,
not room admission, two-browser signaling, WebRTC data channels, or an online
match. The separate service and peer tests are recorded under
`evidence/online/client-network/` and `evidence/online/client-match/`.
