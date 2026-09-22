# QA HUD current r03

This directory records the current shared-runtime Web export produced from the workspace after the helper runtime freeze. It is a local QA artifact only; it is not a deployment and has no claim of full browser/UI parity.

- Build: `GODOT_BIN=/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot tools/build_web.sh`
- PCK: see `build-metadata.json` and `index.pck.sha256`
- Runtime/compiler source hashes: `runtime-sha256.json`
- Browser smoke: not run in this export step because the prior DevTools transport was closed.
