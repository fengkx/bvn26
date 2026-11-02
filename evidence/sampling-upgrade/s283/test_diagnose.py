"""Source-bound CFG and fail-closed qualification checks for rank 2 only."""
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

analysis = load('diagnose')
builder = load('build_probe')


class BodyPushQualificationTests(unittest.TestCase):
    def test_locked_replay_and_unknown_execution(self):
        result = analysis.diagnose()
        self.assertEqual(result['historical_events_revalidated'], 5437)
        self.assertIsNone(result['historical_execution_observed'])
        self.assertEqual(result['new_captures'], 0)
        for key in ('production_admitted', 'native_parity_proven', 'observer_qualified',
                    'external_callsite_execution_proved', 'eligibility_fix_proved'):
            self.assertFalse(result[key])

    def test_original_short_circuit_and_operand_order(self):
        projection = analysis.project((HERE / 'original.pcode').read_text())
        window = analysis.source_window(projection)
        self.assertTrue(window['short_circuit_guards_proved'])
        self.assertTrue(window['target_before_receiver_proved'])

    def test_missing_branch_target_rejected(self):
        text = (HERE / 'original.pcode').read_text().replace('If loc192b', 'If locffffff', 1)
        with self.assertRaisesRegex(ValueError, 'unresolved branch'):
            analysis.project(text)

    def test_eager_guard_cannot_substitute(self):
        text = (HERE / 'original.pcode').read_text().replace('loc1ba8:Push "airBody"', 'loc1ba8:And\nPush "airBody"')
        text = text.replace('PushDuplicate\nNot\nIf loc1be0', 'And\nNot\nIf loc1be0')
        with self.assertRaisesRegex(ValueError, 'short-circuit'):
            analysis.source_window(analysis.project(text))

    def test_extra_hit_test_rejected(self):
        text = (HERE / 'original.pcode').read_text().replace('Push "hitTest"\nCallMethod', 'Push "hitTest"\nCallMethod\nPush "hitTest"\nCallMethod')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            analysis.source_window(analysis.project(text))

    def test_full_graph_retains_returns_writes_and_terminal_edges(self):
        p = analysis.project((HERE / 'original.pcode').read_text())
        nodes = p['nodes']
        self.assertTrue(any(n['instruction'] == 'SetMember' for n in nodes))
        self.assertEqual(sum(n['instruction'] == 'Return' for n in nodes), 6)
        self.assertTrue(any(p['exit_index'] in n['successors'] for n in nodes))
        self.assertTrue(all(not n['successors'] for n in nodes if n['instruction'] == 'Return'))
        self.assertTrue(all(0 <= i <= p['exit_index'] for n in nodes for i in n['successors']))

    def test_string_and_number_operands_remain_distinct(self):
        p = analysis.project('DefineFunction2 "on_enterframe", 0 {\nPush "1", 1.0\n}\n')
        self.assertEqual([n['instruction'] for n in p['nodes']], ['Push "1"', 'Push 1'])

    def test_candidate_changes_only_selected_source_callback(self):
        source = next(s['source'] for s in json.loads((analysis.ROOT / 'scripts/fighter/yihu.json').read_text())['scripts'] if s['path'] == builder.BODY).replace('\r\n', '\n')
        candidate = builder.instrument(source)
        self.assertEqual(candidate.replace(builder.callback(candidate), ''), source.replace(builder.callback(source), ''))
        self.assertEqual(builder.callback(candidate)+'\n', (HERE / 'candidate.as').read_text())
        self.assertEqual(builder.callback(candidate).count('.hitTest('), 1)

    def test_function_flags_not_discarded_as_formatting(self):
        original = analysis.project((HERE / 'original.pcode').read_text())
        candidate = analysis.project((HERE / 'candidate.pcode').read_text())
        self.assertNotEqual(original['header'], candidate['header'])

    def test_changed_branch_edge_changes_projection(self):
        text = (HERE / 'original.pcode').read_text()
        self.assertNotEqual(analysis.project(text), analysis.project(text.replace('If loc192b', 'If loc194b', 1)))


if __name__ == '__main__':
    unittest.main()
