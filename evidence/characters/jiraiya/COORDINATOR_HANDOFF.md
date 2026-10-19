# Jiraiya coordinator handoff

- PR: **#34**, https://github.com/fengkx/bvn2_6/pull/34 (base `master`, head `feat/jiraiya`). Opened; not merged.
- Validated branch tip SHA: `bb1b1062420279dd45dcb6dbf38fbcdcbb77ce6c`. The subsequent commit only adds this handoff; obtain the current tip with `git rev-parse feat/jiraiya` or the PR head SHA. A commit cannot embed its own SHA.
- Parity: **10/10 cases, 4,820/4,820 states**, all 14 existing fighter fields exact. Covers combo, cancel-super, interrupt, guard, receive-guard, super-guard, ultimate-guard, side-changing upper super, repeated target-relative warp and held-input rush/contact. The unexercised short-input diagnostic is excluded.
- Shared compiler/runtime: **unchanged**; conditional whole-roster Flash replay not required. `_clear_interrupted_super_preparation` is retained unchanged and explicitly documented in the PR as a Flash deviation.
- Validation: Python **309 passed, 2 skipped**; nine existing Godot checks and dedicated natural-intro/pause/replay/late-input/round-reset smoke pass; local matchmaking typecheck and **31/31** tests pass; verify, handoff, six contract schemas/examples and 18-fighter online fingerprints pass. Existing headless audio shutdown warnings remain documented.
- Evidence: `README.md` (source audit/acceptance), `checks.json`, `comparisons.json`, `cases/`, compressed `traces/`, `source-builds/`, and excluded `diagnostics/`, all under `evidence/characters/jiraiya/`. `docs/STATUS.md`, coverage and task evidence are updated.
- Blockers: none for this partial fighter port. Full audiovisual/browser/AI and exhaustive move/cancel boundaries remain open. Default assist is outside scope. Worker redeployment is deferred; no Worker/Vercel deployment or merge performed.
