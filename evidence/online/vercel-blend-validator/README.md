# Vercel blend-validator upload fix

Base: `a232e08a40b4ad020232fcc3d41d463062ff00c5` (PR #46 squash merge).

The merged Web build copies `tools/importer/visual_blend_modes.py` into its isolated stage, and `build_online_manifest.py` imports it. The root `.vercelignore` excludes `/tools/*` and never re-includes `tools/importer`. Therefore a filtered deployment source upload omits a required build input. Repository-local tests copied that module explicitly and did not exercise this earlier upload boundary.

The fix opens only `tools/importer/visual_blend_modes.py`, retaining the exclusion of other importer tools. The new regression applies gitignore-style matching in a clean temporary repository, checks every required build input, and confirms unrelated importer code remains excluded. It fails on the merged allowlist and passes with the three-line fix. This matches [Vercel's documented upload filtering](https://vercel.com/docs/deployments/vercel-ignore).

Validation: seven build-pipeline tests pass. A real Godot 4.7.2 Web build from 10,813 filtered files passes import, online checks, export and final manifest validation. The local sidecar identifies tested code commit `fd89611e0f371d4cf061ac49598ecf219f3bac2d`; its PCK SHA-256 was independently checked. Generated artifacts remain under `/tmp/bvn-vercel-investigation/upload/dist/web/`, not in source control. The evidence-only follow-up commit does not change build inputs. `PROTECTED_FUNCTION_OK`, source integrity and handoff checks pass; no gameplay/compiler/rendering code changed.

Remote failure confirmed by the user-provided log excerpt for deployment `dpl_ARUdjWwfs1HreRi9ZiiuJNdFpVSN` at master `a232e08a`:

```text
Staged Godot source snapshot at 2026-10-21T16:50:35Z: /tmp/bvn26-web-build.3V0dq0/repo/godot
cp: cannot stat '/vercel/path0/tools/importer/visual_blend_modes.py': No such file or directory
Error: [BUILD_UTILS_SPAWN_1] Command "bash tools/build_web.sh" exited with 1
```

Earlier provenance, 11 tests and template binding passed. The file is tracked at the correct path in master; `.vercelignore`, not an uncommitted file or a path typo, removes it from the deployment input. The local regression now also checks that every listed dependency exists and is tracked, in addition to checking upload exclusions. Run it locally or in CI before deployment using the command below.

GitHub's Vercel status for PR #47 commit `592b2bbc26e8b835942e6eb119e951d02dbf1bf5` is SUCCESS (2026-10-21T17:25:08Z): https://vercel.com/vito-leungs-projects/bvn2-6/FQyBvnELGJnJkwWrwCjBubaUVfFq . This confirms the fixed upload builds on Vercel. The follow-up only strengthens local tests and records the supplied log; it changes no uploaded build input. Direct CLI log access remains unauthenticated; the original failure excerpt above came from the user.

This is a code-fix PR, not an infrastructure retry. No production redeploy or merge was performed. Production acceptance remains pending merge and a successful deployment whose `build-metadata.json.gitCommit` equals the resulting master commit.

Reproduce the focused checks from the repository root:

```sh
python3 -m unittest tools.tests.test_build_web_pipeline
python3 evidence/characters/juggo/check_protected.py
python3 tools/verify.py
python3 tools/check_handoff.py
```

For the real build, select tracked files using `.vercelignore` rules into a temporary directory without `.git`, set `VERCEL_GIT_COMMIT_SHA` to the tested commit, and run `bash tools/build_web.sh` there. On macOS set `GODOT_BIN` and `TEMPLATE_DIR` to the installed Godot 4.7.2 editor and Web templates. The upload count, build log, sidecar and checks are preserved beside this report.

## Automatic upload dependency guard

The review follow-up replaces the manually maintained tool list with a scan starting at `tools/build_web.sh`: literal live/staged paths and shell for-list copy sites seed a recursive Python AST import closure, including relative imports and package initializers. Literal Python script references are also followed. The only explicit supplement is `godot/project.godot`; generated output and optional evidence publishing paths are excluded. Unresolved shell input substitutions fail with an actionable assertion instead of silently disappearing from the required set. This is a static guard for the pipeline's literal-path conventions, not a general Bash or Python interpreter.

The discovered closure also includes `tools/importer/__init__.py`, now allowed through the upload filter. A synthetic regression adds new run/copy inputs and transitive/relative imports without editing any dependency list, and demonstrates that an excluded transitive module is detected. Eight pipeline tests, the protected gate, source integrity and handoff checks pass.
