"""Reject promotion of AS2 aliases and source order to native lifetime proof."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s307', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ResolverBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tarfile.open(HERE.parent / 's261/native-build.tar.gz') as archive:
            cls.source = archive.extractfile(audit.MEMBER).read().decode()
        cls.bounds = json.loads((HERE / 'source-bounds.json').read_text())
        cls.report = audit.diagnose()

    def test_locked_capture_not_new_native_proof(self):
        self.assertEqual(self.report['retained_capture']['events'], 8290)
        self.assertEqual([r['sequence'] for r in self.report['reference_window']['events']], list(range(36, 49)))
        self.assertTrue(all(v is None for v in self.report['native_observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'slot_reference_proved',
                    'allocation_identity_proved', 'actual_native_controls_executed',
                    'absence_of_possible_resolver_proved'):
            self.assertIs(self.report[key], False)
        self.assertEqual(self.report['m0_02_status'], 'pending')

    def test_distinct_as2_routes_do_not_resolve_native_identity(self):
        source = self.report['source_audit']
        self.assertNotEqual(source['reference_routes']['saved_reference'], source['reference_routes']['depth_slot'])
        self.assertFalse(source['independent_native_resolvers_derived'])
        for key in ('native_layout', 'loaded_module_binding', 'ordered_pool_generations'):
            self.assertIsNone(source[key])

    def test_property_delete_cannot_be_clear_control(self):
        control = self.report['control_obligations']['retained_content_clear']
        self.assertEqual(control['historical_signal']['available_as2_control'], 'retained_content_deleted')
        self.assertFalse(control['qualified'])
        self.assertIsNone(control['observed_native_generations'])
        with self.assertRaisesRegex(ValueError, 'changed archived source'):
            audit.audit_source(self.source.replace('delete replacement.identity;', 'replacement.unloadMovie();'), self.bounds)

    def test_changed_reference_route_rejected(self):
        for old, new in [('var saved = _global.s261Receiver;', 'var saved = parent.AImain;'),
                         ('var occupant = parent.getInstanceAtDepth(_global.s261Depth);', 'var occupant = saved;')]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                audit.audit_source(self.source.replace(old, new), self.bounds)

    def test_reordered_remove_create_rejected(self):
        changed = self.source.replace('saved.removeMovieClip();', 'SWAP').replace(
            'var replacement = host.createEmptyMovieClip("slot", 1);', 'saved.removeMovieClip();').replace(
            'SWAP', 'var replacement = host.createEmptyMovieClip("slot", 1);')
        with self.assertRaises(ValueError):
            audit.audit_source(changed, self.bounds)

    def test_truncated_function_rejected(self):
        bounds = copy.deepcopy(self.bounds)
        bounds['functions'][1]['last_line'] -= 1
        with self.assertRaisesRegex(ValueError, 'incomplete function'):
            audit.audit_source(self.source, bounds)

    def test_native_relabel_rejected(self):
        bounds = copy.deepcopy(self.bounds)
        bounds['kind'] = 'independent_native_resolvers'
        with self.assertRaisesRegex(ValueError, 'not a native resolver'):
            audit.audit_source(self.source, bounds)

    def test_complete_source_retains_observer_effects(self):
        functions = self.report['source_audit']['functions']
        describe = '\n'.join(r['text'] for r in functions[0]['lines'])
        self.assertIn('children.sort();', describe)
        self.assertIn('escape(String(mc))', describe)
        observe = '\n'.join(r['text'] for r in functions[1]['lines'])
        self.assertIn('receiver.__s261Token =', observe)
        self.assertEqual(observe.count('root.aiEvent("aimain_object"'), 4)

    def test_proof_gates_independently_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, code in audit.REQUIREMENTS.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output',
                                         str(Path(directory) / 'report.json'), '--require-' + name],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stderr)

    def test_exclusions_preserved(self):
        self.assertTrue(set(('pointer-only identity', '0->1 alias', 'token-loss identity',
                             'unloaded exemption', 'import inventory as runtime proof',
                             'property deletion as content clearing', 'ranks 1-7 and 9'))
                        <= set(self.report['exclusions_enforced']))


if __name__ == '__main__':
    unittest.main()
