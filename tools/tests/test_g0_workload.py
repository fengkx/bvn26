"""Instrumentation generation and exclusive-sample reporting regressions."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('g0', ROOT / 'tools/build_g0_workload.py')
g0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g0)


analysis_spec = importlib.util.spec_from_file_location('analyze', ROOT / 'tools/analyze_g0_workload.py')
analysis = importlib.util.module_from_spec(analysis_spec)
analysis_spec.loader.exec_module(analysis)


class G0Tests(unittest.TestCase):
    def test_union_does_not_double_count_nested_or_overlapping_display(self):
        self.assertEqual(analysis.union_duration([[10, 70], [20, 40], [60, 100], [120, 130]]), 100)
        self.assertEqual(analysis.union_duration([]), 0)
        with self.assertRaises(ValueError): analysis.union_duration([[4, 3]])

    def test_report_refuses_absent_instrumentation(self):
        ticks = [{'tick': i, 'advance_total_us': 0} for i in range(1, 901)]
        with self.assertRaisesRegex(ValueError, 'all advancement'):
            analysis.analyze({'samples': [{'ticks': ticks}]})
        with self.assertRaisesRegex(ValueError, 'Missing'):
            analysis.analyze({'samples': [{'ticks': ticks[:-1]}]})

    def test_quantiles_come_from_paired_differences(self):
        totals, materials = [1000, 900, 100], [900, 0, 90]
        self.assertEqual(analysis.stats([a-b for a,b in zip(totals, materials)])['p95'], 900)
        self.assertNotEqual(900, analysis.stats(totals)['p95'] - analysis.stats(materials)['p95'])

    def test_complete_report_and_invalid_submit_join(self):
        rows = []
        for i in range(1, 901):
            tick = {'tick': i, 'segment': 'normal', 'advance_total_us': 200,
                    'materialize_in_advance_us': 100, 'simulation_excluding_materialize_us': 100,
                    'input_sample_us': i * 1000, 'input_to_submit_us': 500,
                    'display_status': 'submitted', 'super_active': i == 500,
                    'helper_visible': False, 'action_after': 'standing',
                    'display_spans_us': [[i * 1000, i * 1000 + 100]]}
            rows.append({'ticks': [tick], 'latest_tick': i, 'submit_us': i * 1000 + 500,
                         'submit_start_us': i * 1000 + 400, 'submit_interval_wall_us': 100,
                         'display_spans_us': [], 'display_script_exclusive_us': {}, 'render_cpu_ms': .1})
        report = {'samples': rows}
        summary = analysis.analyze(report)
        self.assertFalse(summary['g0_passed'])
        self.assertEqual(summary['materialize_display_submit_wall_union_us']['p95'], 200)
        self.assertEqual(summary['segments']['observed_heavy_effect']['advance_total_us']['n'], 1)
        rows[0]['ticks'][0]['input_to_submit_us'] = 700
        with self.assertRaisesRegex(ValueError, 'Latency'):
            analysis.analyze(report)

    def test_wrapper_closes_after_early_return(self):
        source = 'func work() -> void:\n\tif true: return\n\tpass\n'
        result = g0.wrap(source, 'work', 'materialize')
        self.assertIn('_g0_originalwork()\n\tpreload("res://g0/timing.gd").end()', result)
        self.assertTrue(result.endswith(source.replace('func work', 'func _g0_originalwork')))

    def test_refuse_changed_signature(self):
        with self.assertRaises(ValueError): g0.wrap('func work() -> int:\n\treturn 1\n', 'work', 'draw')
        with self.assertRaises(ValueError): g0.wrap('', 'work', 'draw')

    def test_tape_complete_deterministic_single_player(self):
        tape = g0.workload()
        self.assertEqual(tape, g0.workload())
        self.assertEqual([x['tick'] for x in tape], list(range(1, 901)))
        self.assertEqual({x['segment'] for x in tape}, {'warmup', 'normal', 'heavy_candidate'})
        for row in tape:
            self.assertFalse(any(row['players']['p2'].values()))
            for player in row['players'].values(): self.assertEqual(set(player), set(g0.BUTTONS))
        self.assertTrue(tape[600]['players']['p1']['special'])

    def test_runtime_targets_are_present(self):
        for file, method, kind, args in [('main.gd', '_advance_fight', 'advance', 'recorded_events, root_observer, event_supplier'),
                                          ('timeline_preview.gd', 'materialize_display', 'materialize', '')]:
            source = (ROOT / 'godot' / file).read_text()
            self.assertIn('_g0_original' + method, g0.wrap(source, method, kind, args))


if __name__ == '__main__': unittest.main()
