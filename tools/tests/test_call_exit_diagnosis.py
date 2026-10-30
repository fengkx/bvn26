"""Keep removal evidence separate from a witnessed AS call return."""
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.sampling_callsite import collect_calls
from tools.sampling_chad_lifecycle import collect_lifecycle
from tools.sampling_native import validate_capture

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/sampling-upgrade/s252'


class CallExitDiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = gzip.decompress((EVIDENCE / 'native-capture.log.gz').read_bytes()).decode().splitlines()
        cls.metadata = json.loads((EVIDENCE / 'native-build.json').read_text())

    def test_recomputed_native_and_source_diagnosis(self):
        spec = importlib.util.spec_from_file_location('s252_diagnosis', EVIDENCE / 'diagnose.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual = module.diagnose()
        retained = json.loads(gzip.decompress((EVIDENCE / 'diagnosis.json.gz').read_bytes()))
        self.assertEqual(actual, retained)
        self.assertFalse(actual['exit_model_fix_proved'])

    def test_removed_receiver_does_not_satisfy_exit_gate(self):
        report = collect_lifecycle(self.lines)
        self.assertEqual(report['observations'][-1]['occupant'], 'undefined')
        self.assertFalse(report['exit_observations_complete'])
        with self.assertRaisesRegex(ValueError, 'incomplete/reentrant'):
            collect_calls(self.lines, self.metadata['callsite_specification'])

    def test_each_observed_boundary_remains_required(self):
        for phase in ('caller_before', 'callee_enter', 'goto_before', 'root_sample'):
            changed = [line for line in self.lines if '|chad_lifecycle|' + phase + ',' not in line]
            with self.subTest(phase=phase):
                with self.assertRaisesRegex(ValueError, 'missing discriminator'):
                    collect_lifecycle(changed)
                with tempfile.TemporaryDirectory() as temp:
                    trace = Path(temp) / 'native.log'
                    trace.write_text('\n'.join(changed) + '\n')
                    with self.assertRaisesRegex(ValueError, 'missing/duplicate/out-of-order'):
                        validate_capture(self.metadata['move_case'], self.metadata, trace)

    def test_replacement_identity_is_not_the_observed_receiver(self):
        instance = collect_lifecycle(self.lines)['observations'][0]['saved_path'].rsplit('.', 1)[1]
        changed = [line.replace(instance, 'instance999')
                   if '|chad_lifecycle|root_sample,' in line else line for line in self.lines]
        with self.assertRaisesRegex(ValueError, 'changed tracked receiver identity'):
            collect_lifecycle(changed)


if __name__ == '__main__':
    unittest.main()
