"""Profiles must not inherit diagnostics or make an observation copy clean."""
import inspect
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

from tools.probes.build_ai_reference import build, validate_profile
from tools.probes.helper_observation_profile import patch, flags, ROOT_SITES
from tools.probes.helper_init_observer import SITES

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS = {key: p.default for key, p in inspect.signature(build).parameters.items()}


class BuilderProfileTests(unittest.TestCase):
    def options(self):
        values = {key: value for key, value in DEFAULTS.items() if value is not inspect.Parameter.empty}
        values.update(profile="helper-observation", helper_init_observer=True, p1_helper="woailuo", p2_helper="kon")
        return values

    def test_default_fails_before_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "absent"
            with self.assertRaisesRegex(ValueError, "Explicit --profile"):
                build(Path(directory) / "unused.jar", output, "test", 600)
            self.assertFalse(output.exists())

    def test_unknown_profile_and_implicit_helper_fail(self):
        options = self.options()
        for key, value in [("profile", "typo"), ("helper_init_observer", False), ("p1_helper", None)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_profile(dict(options, **{key: value}), DEFAULTS)

    def test_every_boolean_diagnostic_is_rejected_in_observation(self):
        options = self.options()
        validate_profile(options, DEFAULTS)
        for key, default in DEFAULTS.items():
            if default is False and key != "helper_init_observer":
                with self.subTest(key=key), self.assertRaises(ValueError):
                    validate_profile(dict(options, **{key: True}), DEFAULTS)
        for key, value in [("move_case", Path("fake")), ("mode_probe", 3), ("p1_character", "白哉"),
                           ("helper_probe", "kon"), ("dash_duration", 99)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_profile(dict(options, **{key: value}), DEFAULTS)

    def test_diagnostic_requires_each_consent(self):
        required = ["diagnostic_auto_start", "diagnostic_key_injection", "diagnostic_trace_hooks"]
        options = dict(self.options(), profile="diagnostic", **dict.fromkeys(required, True))
        validate_profile(options, DEFAULTS)
        for key in required:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_profile(dict(options, **{key: False}), DEFAULTS)

    def test_patch_scope_and_no_injected_control_flow(self):
        changed = set()
        additions = []
        import difflib
        for name in ['main', 'fighter/fz/woailuo', 'fighter/fz/kon']:
            bundle = json.loads((ROOT / f'scripts/{name}.json').read_text())
            for row in bundle['scripts']:
                source = row['source']
                updated = patch(name, row['path'], source, 'offline-test')
                if source != updated:
                    changed.add((name, row['path']))
                    additions.extend(line[1:] for line in difflib.ndiff(source.splitlines(), updated.splitlines()) if line.startswith('+ '))
                if row['path'] == 'frame_10/DoAction.as':
                    self.assertEqual(source, updated)
        self.assertEqual(changed, set(SITES) | {('main', p) for p in ROOT_SITES})
        added = '\n'.join(additions)
        for forbidden in ['gotoAndPlay', 'gotoAndStop', 'onEnterFrame', 'aiKeyDown', 'aiHeld',
                          'aiBodyBoundary', 'Math.random', 'Key.isDown', 'fscommand', 'fighterDir =']:
            self.assertNotIn(forbidden, added)
        self.assertIn('startFight-source-tail', added)
        self.assertIn('|-1|-1|', added)
        self.assertTrue(all(value is False for value in flags().values()))

    def test_cli_refusals_have_explicit_false_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "absent"
            base = [sys.executable, str(ROOT / "tools/probes/build_ai_reference.py"),
                    "--ffdec", "unused.jar", "--output", str(output), "--run-id", "offline-test"]
            for extra in ([], ["--profile", "diagnostic"],
                          ["--profile", "helper-observation", "--helper-init-observer",
                           "--p1-helper", "woailuo", "--p2-helper", "kon", "--body-boundaries"]):
                with self.subTest(extra=extra):
                    result = subprocess.run(base + extra, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    report = json.loads(result.stdout)
                    for key in flags():
                        self.assertIs(report[key], False)
                    self.assertEqual(report["status"], "build_refused")
                    self.assertFalse(output.exists())

    def test_changed_logger_source_refused(self):
        for path in ROOT_SITES:
            with self.assertRaises(ValueError):
                patch('main', path, 'changed', 'offline-test')


if __name__ == '__main__':
    unittest.main()
