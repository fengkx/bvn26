"""Protect observed negatives without assuming removal is a VM return."""
import gzip
import importlib.util
import json
from pathlib import Path
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s257'


def load(name):
    spec = importlib.util.spec_from_file_location('s257_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContinuationDiscriminatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load('diagnose')
        cls.builder = load('build_probe')
        cls.lines = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode().splitlines()
        cls.report = cls.module.diagnose()

    def test_portable_evidence(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for field in ('production_admitted', 'native_parity_proven', 'exit_model_fix_proved',
                      'positive_post_goto_witness'):
            self.assertFalse(self.report[field])
        self.assertEqual(self.report['actor_comparison'], {'rows': 122, 'exact_tick_payload_equal_s252': True})

    def test_positive_control_and_retained_absence(self):
        rows = self.report['observations']
        self.assertEqual([r['tick'] for r in rows], [10, 11, 12])
        for row in rows[1:]:
            self.assertEqual((row['before'], row['control'], row['post'], row['observer_entry']),
                             ('1', '1', '0', '0'))
        self.assertEqual(self.report['lifecycle']['missing_boundaries'],
                         ['goto_after', 'callee_exit', 'caller_after'])
        self.assertEqual(len(self.report['incomplete_invocations']), 1)

    def test_missing_duplicate_identity_or_control_rejects(self):
        selected = next(line for line in self.lines if '|11|s257_witness|' in line)
        variants = [[line for line in self.lines if line != selected], self.lines + [selected]]
        for old, new in [('s257-chad-normal-goto', 'wrong-object'), (',1,1,0,0', ',1,0,0,0')]:
            variants.append([line.replace(old, new) if line == selected else line for line in self.lines])
        for lines in variants:
            with self.assertRaises(ValueError):
                self.module.observations(lines)

    def test_raw_missing_sequence_rejected(self):
        import tempfile
        metadata = json.loads((HERE / 'native-build.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'raw.log'
            path.write_text('\n'.join(self.lines[:50] + self.lines[51:]) + '\n')
            with self.assertRaises(ValueError):
                self.module.validate_capture(metadata['move_case'], metadata, path)

    def test_actual_compiled_register_writes_and_negative(self):
        callee = gzip.decompress((HERE / 'pcode/chad/DefineSprite_16/frame_1/DoAction.pcode.gz').read_bytes()).decode().replace('\r\n', '\n')
        hooks = gzip.decompress((HERE / 'pcode/main/frame_1/DoAction.pcode.gz').read_bytes()).decode().replace('\r\n', '\n')
        self.module.compiled_sites(callee, hooks)
        for changed_callee, changed_hooks in [(callee.replace('Push "post"', 'Push "other"'), hooks),
                                              (callee, hooks.replace('Push "observerEntry"', 'Push "other"'))]:
            with self.assertRaises(ValueError):
                self.module.compiled_sites(changed_callee, changed_hooks)

    def test_unchanged_unqualified_caller_bytecode(self):
        relative = self.module.HANDLER.removesuffix('.as') + '.pcode.gz'
        old = gzip.decompress((HERE.parent / 's252/pcode' / relative).read_bytes())
        new = gzip.decompress((HERE / 'pcode/chad' / relative).read_bytes())
        self.assertEqual(old, new)
        with tarfile.open(HERE / 'native-build.tar.gz') as archive:
            caller = archive.extractfile('patches/fighter/chad/' + self.module.HANDLER).read().decode()
            self.assertEqual(caller.count('doAllAction();'), 1)
            self.assertEqual(caller.count('gameRunning()'), 1)

    def test_patcher_rejects_missing_or_duplicate_boundary(self):
        for patcher in (self.builder.patch_callee, self.builder.patch_root, self.builder.patch_hooks):
            with self.assertRaises(ValueError):
                patcher('')
        source = '   _global.bvnChadObserve("root_sample", undefined);'
        with self.assertRaises(ValueError):
            self.builder.patch_root(source + source)


if __name__ == '__main__':
    unittest.main()
