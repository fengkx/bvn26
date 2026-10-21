# Vercel blend-validator upload fix

Base: `a232e08a40b4ad020232fcc3d41d463062ff00c5` (PR #46 squash merge).

The merged Web build copies `tools/importer/visual_blend_modes.py` into its isolated stage, and `build_online_manifest.py` imports it. The root `.vercelignore` excludes `/tools/*` and never re-includes `tools/importer`. Therefore a filtered deployment source upload omits a required build input. Repository-local tests copied that module explicitly and did not exercise this earlier upload boundary.

The fix opens only `tools/importer/visual_blend_modes.py`, retaining the exclusion of other importer tools. The new regression applies gitignore-style matching in a clean temporary repository, checks every required build input, and confirms unrelated importer code remains excluded. It fails on the merged allowlist and passes with the three-line fix. This matches [Vercel's documented upload filtering](https://vercel.com/docs/deployments/vercel-ignore).

Validation: seven build-pipeline tests pass. A real Godot 4.7.2 Web build from 10,813 filtered files passes import, online checks, export and final manifest validation. The local sidecar identifies tested code commit `fd89611e0f371d4cf061ac49598ecf219f3bac2d`; its PCK SHA-256 was independently checked. Generated artifacts remain under `/tmp/bvn-vercel-investigation/upload/dist/web/`, not in source control. The evidence-only follow-up commit does not change build inputs. `PROTECTED_FUNCTION_OK`, source integrity and handoff checks pass; no gameplay/compiler/rendering code changed.

Remote evidence limitation: GitHub reports deployment `dpl_ARUdjWwfs1HreRi9ZiiuJNdFpVSN` failed, and the production metadata still identifies `3a3bafd816039d62b557950e56c79c1436405ad7`. This environment has no Vercel CLI credentials; `inspect --logs` requests login and the unauthenticated events API returns 403. The missing input is reproduced locally, but the original remote log's first error has not been observed. Do not describe the remote logs as inspected successfully. Login or the original failed-log excerpt is still needed to confirm that first error.

This is a code-fix PR, not an infrastructure retry. No production redeploy or merge was performed. Production acceptance remains pending merge and a successful deployment whose `build-metadata.json.gitCommit` equals the resulting master commit.

Reproduce the focused checks from the repository root:

```sh
python3 -m unittest tools.tests.test_build_web_pipeline
python3 evidence/characters/juggo/check_protected.py
python3 tools/verify.py
python3 tools/check_handoff.py
```

For the real build, select tracked files using `.vercelignore` rules into a temporary directory without `.git`, set `VERCEL_GIT_COMMIT_SHA` to the tested commit, and run `bash tools/build_web.sh` there. On macOS set `GODOT_BIN` and `TEMPLATE_DIR` to the installed Godot 4.7.2 editor and Web templates. The upload count, build log, sidecar and checks are preserved beside this report.
