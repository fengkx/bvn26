"""Synthetic adapter fixtures, never evidence of native gameplay parity."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import sampling_matrix as matrix
from tools import sampling_native as native


class NativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.campaign = self.root / 'campaign'
        self.entry = matrix.generate(self.campaign, ['didala'], True)['cases'][0]
        self.case_path = self.campaign / 'cases' / (self.entry['id'] + '.json')
        self.case = json.loads(self.case_path.read_text())
        self.build = self.root / 'build'
        (self.build / 'game').mkdir(parents=True)
        (self.build / 'game/main.swf').write_bytes(b'synthetic instrumented SWF')
        (self.build / 'instrumentation.diff').write_text('synthetic probe diff')
        self.engine = self.root / 'synthetic-player'
        self.engine.write_bytes(b'fixture only; not Flash Player')
        self.metadata = {'run_id': 'fixture-s27', 'move_case': self.case,
                         'dynamic_move_case': False, 'frames_after_ready': 60,
                         'configuration': {'p1': '迪达拉', 'p2': '一护', 'modo': 3, 'p2cpu': False,
                                           'stage': '现世', 'p1sf': '我爱罗', 'p2sf': '魂'},
                         'sources_sha256': {p: native.sha(native.ROOT / p) for p in
                                            ('game/main.swf', 'game/fighter/didala.swf', 'game/fighter/yihu.swf')},
                         'outputs_sha256': {'game/main.swf': native.sha(self.build / 'game/main.swf')},
                         'instrumentation_sha256': native.sha(self.build / 'instrumentation.diff')}
        self.save_metadata()
        self.trace = self.root / 'capture.log'
        lines = []
        for tick in range(61):
            for slot in ('p1', 'p2'):
                fields = [slot] + ['0'] * 14
                fields[9] = 'true'
                value = ','.join(fields)
                lines.append(f'AIREF|fixture-s27|{len(lines)+1}|0|{tick}|{tick}|state|{value}')
        lines.append('AIREF|fixture-s27|123|0|60|60|done|')
        self.lines = lines
        self.trace.write_text('\n'.join(lines) + '\n')
        self.receipt = self.root / 'receipts' / (self.case['id'] + '.json')

    def save_metadata(self):
        (self.build / 'build.json').write_text(json.dumps(self.metadata))

    def seal(self):
        return native.seal(self.case_path, self.build, self.trace, self.engine, self.receipt)

    def test_positive_required_native_gate_and_report_binding(self):
        self.seal()
        bindings = matrix.require_native_evidence([self.entry], self.campaign, self.receipt.parent)
        self.assertEqual(bindings, {self.case['id']: native.sha(self.receipt)})
        rows = [dict.fromkeys(matrix.STATE_FIELDS, 0) | {'tick': t, 'slot': s, 'touch': True}
                for t in range(61) for s in ('p1', 'p2')]
        camera = [{'tick': t, 'x': 0, 'y': 0} for t in range(61)]
        def execute(engine, paths, output):
            (output / (self.case['id'] + '.json')).write_text(json.dumps(rows))
            (output / (self.case['id'] + '.json.presentation.json')).write_text(json.dumps(camera))
            return [{'id': self.case['id'], 'executed': True}]
        with patch.object(matrix, 'execute_batch', side_effect=execute):
            report = matrix.run(self.campaign, self.root / 'run', Path('/fixture'),
                                [self.case['id']], self.receipt.parent)
        self.assertEqual(report['native_receipts'], bindings)
        self.assertFalse(report['execution_coverage_complete'])
        self.assertFalse(report['native_parity_proven'])
        self.assertFalse(report['production_admitted'])
        with self.assertRaisesRegex(ValueError, 'missing native evidence'):
            matrix.require_full_coverage(self.campaign, self.root / 'run', self.receipt.parent)

    def test_capture_command_reuses_native_player_and_rejects_failed_capture(self):
        args = ['sampling_native', '--case', str(self.case_path), '--build', str(self.build),
                '--trace', str(self.trace), '--receipt', str(self.receipt), '--allow-window-activation']
        with patch('sys.argv', args), patch.object(native.player, 'preflight'), \
                patch.object(native.player, 'player_binary', return_value=self.engine), \
                patch.object(native.player, 'capture', return_value=True) as capture:
            native.main()
            capture.assert_called_once()
        native.validate(self.case_path, self.receipt)
        self.receipt.unlink()
        with patch('sys.argv', args), patch.object(native.player, 'preflight'), \
                patch.object(native.player, 'capture', return_value=False), \
                patch('sys.stderr'), self.assertRaises(SystemExit):
            native.main()
        self.assertFalse(self.receipt.exists())

    def test_check_rejects_report_receipt_substitution(self):
        self.seal()
        output = self.root / 'run'
        output.mkdir()
        (output / 'report.json').write_text(json.dumps({'native_receipts': {}}))
        with patch.object(matrix, 'require_native_evidence', return_value={self.case['id']: 'expected'}):
            with self.assertRaisesRegex(ValueError, 'receipt bindings changed'):
                matrix.require_full_coverage(self.campaign, output, self.receipt.parent)

    def test_missing_receipt_rejects(self):
        with self.assertRaisesRegex(ValueError, 'missing native evidence'):
            matrix.require_native_evidence([self.entry], self.campaign, self.receipt.parent)

    def test_case_and_dynamic_fixture_mismatch_reject(self):
        for change in ('case', 'dynamic'):
            with self.subTest(change=change):
                self.metadata['move_case'] = self.case.copy()
                self.metadata['move_case']['id'] = 'wrong' if change == 'case' else self.case['id']
                self.metadata['dynamic_move_case'] = change == 'dynamic'
                self.save_metadata()
                with self.assertRaises(ValueError):
                    self.seal()

    def test_missing_duplicate_foreign_and_incomplete_events_reject(self):
        variants = [self.lines[:-1], self.lines[:20] + self.lines[21:],
                    self.lines[:20] + [self.lines[19]] + self.lines[21:],
                    [s.replace('fixture-s27', 'foreign') for s in self.lines],
                    [s.replace('state|p1,', 'state|') for s in self.lines],
                    self.lines[:-1] + [self.lines[-1].replace('|done|', '|timeout|')]]
        for lines in variants:
            with self.subTest(lines=lines[:1]):
                self.trace.write_text('\n'.join(lines))
                with self.assertRaises(ValueError):
                    self.seal()

    def test_changed_artifacts_reject_even_when_trace_still_complete(self):
        self.seal()
        for path in (self.trace, self.engine, self.build / 'game/main.swf', self.build / 'instrumentation.diff'):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                try:
                    with self.assertRaises(ValueError):
                        native.validate(self.case_path, self.receipt)
                finally:
                    path.write_bytes(original)

    def test_wrong_setup_duration_and_nonfinite_state_reject(self):
        for field, value in (('frames_after_ready', 59), ('configuration', {})):
            original = self.metadata[field]
            self.metadata[field] = value
            self.save_metadata()
            with self.assertRaises((ValueError, KeyError)):
                self.seal()
            self.metadata[field] = original
        self.save_metadata()
        for old, new in (('state|p1,0,0,', 'state|p1,0,NaN,'), (',true,', ',false,')):
            self.trace.write_text('\n'.join(self.lines).replace(old, new))
            with self.assertRaises(ValueError):
                self.seal()

    def test_missing_source_binding_rejects(self):
        del self.metadata['sources_sha256']['game/fighter/didala.swf']
        self.save_metadata()
        with self.assertRaisesRegex(ValueError, 'source SWF'):
            self.seal()

    def test_receipt_cannot_claim_parity(self):
        data = self.seal()
        data['native_parity_proven'] = True
        self.receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            native.validate(self.case_path, self.receipt)


if __name__ == '__main__':
    unittest.main()
