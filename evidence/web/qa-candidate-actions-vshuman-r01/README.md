# QA-only candidate action inputs

This archive records a separate Web build and headless Chromium run for the candidate-character I/O/N5/N6 input check. It did not alter the production roster or production package. The wrapper chooses the fighters/helpers and mode directly, then lets the normal map confirmation, intro, Ready, input, controller, and combat paths run. It is not evidence for the title-to-selection menu path or Flash parity.

- QA URL during capture: `http://127.0.0.1:8788/`
- PCK SHA256: `fe425bcdd5e8e26a0f600e4491efca605bae7d9cfb23fdd15e37ff250831e0c5`
- Runtime SHA256: `main.gd` `8ef3f927c78426fbd50b2ed700544aff1b31d2727f59adf018a357a900ca8c7d`; `helper_runtime.gd` `4a0f08ff087a498e9b15ed37bc166e2af9580ed4aa6b8e7853eaf742ce4f94f7`; `fighter_runtime.gd` `feb1a03f8a79ef9b9a0e1521d59b4ee57adb7501414c5856cb2c6ded4aefe5ac`.
- The isolated entry wrapper is `qa_web_input_entry.gd`; its fixture selects P1 Byakuya/Kon and P2 Lee/Gaara, mode 3, and disables CPU control for both. It seeds each fighter to 300 energy only after the ordinary map transition and when `battle_intro.active` is false. The N6 test uses a fresh page reload and a second completed Ready so Lee again begins at the explicit QA energy precondition.
- All four actions used separate browser CDP key down/up events with a 320ms hold. DOM observation captured `isTrusted=true`, canvas target, visibility/focus, code, keyCode, and keypad location. The JSONL console files preserve the actual DevTools console callback text as JSON records; game-log JSON files are exports from the in-app diagnostics button.
- `capture-action-session.mjs` is the small capture driver used for each action; it expects the owned headless QA Chrome at CDP port 9230 and its page target ID embedded in the script. It writes one screenshot, key-event trace, console JSONL, and in-app game log per invocation. The page ID is session-specific, so update that constant when starting a new isolated browser session.

## Results

- P1 I: `04-p1-i-super-*` shows the live action `空中必杀` at source frame 512 and later hit settlements against Lee. The observation is one triggered action, not a full source-timeline parity claim.
- P1 O: `05-p1-o-summon-*` records `helper_activate_魂` and `summon_剑八`; the helper state is attacking at the captured snapshot.
- P2 N5: `06-p2-n5-special-*` records the trusted Numpad5 event and Lee in `必杀` at source frame 615. The energy values are the observed before/after snapshot, not a claim about a fixed action cost.
- P2 N6: `10-p2-n6-summon-*` records trusted Numpad6, `helper_activate_我爱罗`, and `summon_天天`; the selected Gaara helper is attacking at the captured snapshot. This was a distinct fresh Ready run at the QA-seeded 300 energy level.

`03-ready-hud.png` and `09-n6-ready-hud.png` show the actual post-intro HUD. `01-map-selection.png` and `07-reloaded-qa-map.png` document the map step. Each action has a PNG, key-event JSON, DevTools console JSONL, and in-app game-log JSON. `action-observations.json` provides the extracted per-action summary; `SHA256SUMS.txt` binds the archived files.

The export completed and the package ran. `export-r02.log` contains a Godot editor-settings write failure for the user's external settings path, but no script parse error or failed resource load. The candidate title-menu mode-navigation issue remains outside this fixture's coverage.

Repository integrity checks after adding this evidence passed: `tools/verify.py`, `tools/check_handoff.py`, `tools/validate_contracts.py`, and `git diff --check`. The only tracked-worktree changes made for this subtask are this evidence directory; shared runtime/roster files were not edited here.
