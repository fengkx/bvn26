# M0 Godot 与 Web 环境证据

状态：`M0-01 in_progress`  
记录日期：2026-09-04（Asia/Shanghai）

## 基准设备

- Hardware: MacBook Pro (Mac15,7), Apple M3 Pro, 12 cores, 36 GB RAM
- OS: macOS 15.7.5 (24G624), arm64
- Stage baseline: 600 x 400
- Simulation frequency: 30 Hz

设备序列号、硬件 UUID 等私有标识不写入仓库。

## Godot 工具链

- Editor: Godot `4.7.2.stable.official.ed1daf0bf`
- Download source: official Godot 4.7.2 stable archive
- macOS editor archive SHA-256: `c58a24e31d720be9d62f60cb5627c4e695fb72f21b0cfe1bc9ccaa9a3b3ba63e`
- export templates archive SHA-256: `f298490b8d44d934be425a5a65a51bf15f422428b229a06a6e11d9ffea248011`
- single-thread debug Web template SHA-256: `08962aefef811b603541d7951ac67ef00413aad2d978855183c28adee98f626a`
- single-thread release Web template SHA-256: `d3ee2f08cef0cf3cf6678a6355a92a8db48ccdd35cbd2e8bfd5f0e8a0b4032a0`
- Project renderer: Compatibility
- Web preset: single-threaded, GDExtension disabled

The editor and templates were downloaded to a temporary tool directory and the
user-level Godot template cache. They are not repository contents.

## Commands and observed results

Headless import and boot:

```text
Godot Engine v4.7.2.stable.official.ed1daf0bf
M0_BOOT_OK {"display_server":"headless","godot":"4.7.2-stable (official)","physics_hz":30}
```

Release Web export:

```text
godot --headless --path godot --export-release Web ../dist/web/index.html
```

The export completed successfully. The generated `dist/web/` was 38 MB and
contained HTML, JavaScript, WASM, PCK, worklet, and icon files. A text scan found
no SWF, ActionScript, Ruffle, or AVM references. `dist/` is generated output and
is intentionally ignored by Git.

Local HTTP loading in the Codex in-app browser produced:

```text
Godot Engine v4.7.2.stable.official.ed1daf0bf
OpenGL API OpenGL ES 3.0 (WebGL 2.0 (OpenGL ES 3.0 Chromium)) - Compatibility
Build configuration: Emscripten 4.0.20, single-threaded, no GDExtension support.
M0_BOOT_OK {"display_server":"web","godot":"4.7.2-stable (official)","physics_hz":30}
```

The canvas was visible and the fixed simulation tick advanced continuously.
The observed backing canvas was 2560 x 1440 at a 1280 x 720 CSS size; the game
viewport kept the 600 x 400 aspect ratio with letterboxing.

## Browser matrix

| Target | Detected version | Result |
|---|---:|---|
| Codex in-app browser | embedded runtime | Boot passed; this is supporting evidence only |
| Google Chrome | 152.0.7977.76 | Passed via isolated DevTools session; scene rendered and `M0_BOOT_OK` observed |
| Safari | 26.4 (20624.1.16.18.2) | Installed; test pending |
| Firefox | stale Homebrew wrapper for 124.0.1 | Broken locally (exit 134); reinstall and test pending |

`M0-01` must remain `in_progress` until Chromium, Firefox, and Safari are each
tested as named targets with complete version and launch logs.

The Chrome check used `tools/test_chromium_web_boot.mjs` against a loopback-only
HTTP server. It verified the visible canvas, captured the native timeline preview,
and observed the same 30 Hz Web boot marker as the embedded-browser check.
