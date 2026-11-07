"""Protect archived dependency provenance without asserting a Flash schedule."""
import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('s319_diagnose', Path(__file__).with_name('diagnose.py'))
D = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D)


class ChannelAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = D.read_sources()

    def test_exact_source_and_unknown_channel(self):
        result = D.channel_audit(self.sources)
        self.assertEqual(result['sink_call_lines'], [6, 11, 15])
        self.assertIsNone(result['independent_live_channel'])
        self.assertIsNone(result['observer_off_surviving_channel'])

    def test_each_serialized_operand_change_rejected(self):
        for operand in ('String(mc)', 'mc.getDepth()', 'mc.s274Generation', 'mc._currentframe'):
            with self.subTest(operand=operand):
                sources = copy.deepcopy(self.sources)
                sources[D.ROOT_MEMBER] = sources[D.ROOT_MEMBER].replace(operand, 'independentValue')
                with self.assertRaises(ValueError):
                    D.channel_audit(sources)

    def test_generation_write_removal_rejected(self):
        sources = dict(self.sources)
        sources[D.ROOT_MEMBER] = sources[D.ROOT_MEMBER].replace('++_root.s274Generation', '0')
        with self.assertRaises(ValueError):
            D.channel_audit(sources)

    def test_calibration_write_changes_rejected(self):
        for flag in ('s274Unloaded2', 's274RetainedEntry2'):
            with self.subTest(flag=flag):
                sources = dict(self.sources)
                sources[D.ROOT_MEMBER] = sources[D.ROOT_MEMBER].replace(flag, 'otherFlag')
                with self.assertRaises(ValueError):
                    D.channel_audit(sources)

    def test_sink_change_rejected(self):
        sources = dict(self.sources)
        sources[D.ROOT_MEMBER] = sources[D.ROOT_MEMBER].replace('_root.aiEvent', '_root.otherEvent', 1)
        with self.assertRaises(ValueError):
            D.channel_audit(sources)

    def test_hook_reordering_rejected(self):
        sources = dict(self.sources)
        sources[D.ENTRY_MEMBER] = 'stop();\n_root.s274Entry(this);\n_root.s262Init(this,1810);\n'
        with self.assertRaises(ValueError):
            D.channel_audit(sources)

    def test_lifecycle_receiver_change_rejected(self):
        for phase in ('load', 'unload'):
            with self.subTest(phase=phase):
                sources = dict(self.sources)
                name = D.LIFE_PREFIX + 'CLIPACTIONRECORD onClipEvent(' + phase + ').as'
                sources[name] = sources[name].replace('(this,', '(_parent,')
                with self.assertRaises(ValueError):
                    D.channel_audit(sources)

    def test_full_diagnosis_remains_unproved(self):
        result = D.diagnose()
        for field in ('production_admitted', 'native_parity_proven', 'observer_qualified',
                      'independent_controls_proved', 'independent_child_clock_proved', 'fresh_capture_eligible'):
            self.assertIs(result[field], False)
        self.assertEqual([r['frame'] for r in result['qualification_matrix']], list(range(1, 11)))
        for row in result['qualification_matrix']:
            for key in ('independent_entry', 'isolated_repeated_target', 'isolated_changed_target',
                        'same_depth_replacement', 'observer_off_on_order'):
                self.assertIsNone(row[key])


if __name__ == '__main__':
    unittest.main()
