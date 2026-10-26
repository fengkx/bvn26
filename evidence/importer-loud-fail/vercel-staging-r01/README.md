# Vercel manifest staging import fix

Base: b26d74f7, branch fix/importer-loud-fail, Draft PR48. No runtime, Flash guards, Worker or production deployment changes.

Root cause: tools/build_web.sh creates a second repository snapshot and explicitly copies importer dependencies into it, but omitted clip_action_fields.py and form_profile_guard.py. The manifest runs from that snapshot, not the upload/checkout where both files exist. The observed missing name is the direct relative import in import_guards.py; clip_action_fields itself has only a standard-library dependency. This is a staging-copy omission, not evidence of broken .vercelignore negation or an ambient PYTHONPATH problem.

Fix: copy those two dependencies and importer/__init__.py into the existing staging package. All three already have explicit .vercelignore inclusions; no upload policy change is needed.

Regression: test_web_manifest_staging.py constructs an isolated input directory from the explicit file inclusions in .vercelignore (not a claim to implement Vercel's entire ignore algorithm), executes the actual tool-copy shell block from build_web.sh, then invokes the staged manifest --help using Python -E -B and an unrelated working directory. This imports every top-level dependency without using the checkout's tools or PYTHONPATH. Before the three-line fix, the test reproduces exactly ModuleNotFoundError: importer.clip_action_fields. After the fix it passes. See before.log / after.log.

Commands and results:

```sh
python3 -m unittest discover -s tools/tests -p test_web_manifest_staging.py
# 1/1 PASS after fix; same test fails before fix
python3 -m unittest discover -s tools/tests -p test_web_diagnostics_metadata.py
# 11/11 PASS
bash -n tools/build_web.sh
# PASS
python3 tools/build_online_manifest.py --check
# Imports succeed; intentional Yihu638/frame1052 wankai rejection, exit1
python3 tools/verify.py
python3 tools/check_handoff.py
# Both PASS
```

The actual Vercel rebuild was not run here. It should now pass this missing-module crash, but the existing 24/26 form acceptance and strict content guards still block the complete preview build. No full Web export or gameplay replay was necessary for this packaging-only change.
