import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.sampling_matrix import cells, fixture, generate, load_campaign, validate_trace, require_full_coverage, STATE_FIELDS


class SamplingMatrixTests(unittest.TestCase):
    def setUp(self):
        self.case = fixture(cells(['didala'])[0])
        self.rows = [dict.fromkeys(STATE_FIELDS, 0) | {'tick': tick, 'slot': slot, 'x': 100, 'y': 0, 'touch': True}
                     for tick in range(61) for slot in ('p1', 'p2')]
        self.camera = [{'tick': tick, 'x': 0, 'y': 0} for tick in range(61)]

    def test_cartesian_coverage_includes_diagonals_and_air(self):
        matrix = cells(['didala', 'pain'])
        self.assertEqual(len(matrix), 648)
        self.assertEqual(len({tuple(c.values()) for c in matrix}), 648)
        air = fixture(next(c for c in matrix if c['posture'] == 'air'))
        self.assertEqual(air['inputs'][0], {'slot': 'p1', 'keys': ['jump'], 'start': 1, 'end': 2})
        self.assertEqual(air['inputs'][-1]['start'], 10)

    def test_generated_tapes_use_existing_native_fixture_encoder(self):
        from urllib.parse import parse_qs
        from tools.probes.move_cases import encode_case
        for cell in cells(['didala']):
            encoded = parse_qs(encode_case(fixture(cell), 'sampling-s01'))
            self.assertEqual(encoded['case_id'], [fixture(cell)['id']])
        cell = dict(fighter='didala', key='dash', direction='up', posture='air', distance='near')
        encoded = parse_qs(encode_case(fixture(cell), 'sampling-s01'))
        self.assertEqual(encoded['windows'], ['1:2:k;10:13:w;10:13:l'])
        self.assertEqual(encoded['p1x'], ['100'])
        self.assertEqual(encoded['p2x'], ['150'])

    def test_valid_observations(self):
        validate_trace(self.case, self.rows, self.camera)

    def test_deleted_and_duplicated_frame_fail_even_with_same_row_count(self):
        for rows in (self.rows[:-1], self.rows[:-1] + [self.rows[-2]]):
            with self.assertRaisesRegex(ValueError, 'fighter observations'):
                validate_trace(self.case, rows, self.camera)

    def test_missing_camera_fails(self):
        with self.assertRaisesRegex(ValueError, 'camera observations'):
            validate_trace(self.case, self.rows, self.camera[:-1])

    def test_failed_air_setup_is_not_air_coverage(self):
        case = copy.deepcopy(self.case)
        case['sampling_cell']['posture'] = 'air'
        with self.assertRaisesRegex(ValueError, 'posture not reached'):
            validate_trace(case, self.rows, self.camera)

    def test_nonfinite_coordinates_fail(self):
        self.rows[5]['x'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'invalid x'):
            validate_trace(self.case, self.rows, self.camera)

    def test_generation_and_missing_matrix_cell_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'campaign'
            generate(path, ['didala'])
            self.assertEqual(len(load_campaign(path)['cases']), 324)
            manifest_path = path / 'matrix.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['cases'].pop()
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'matrix coverage'):
                load_campaign(path)

    def test_changed_tape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'campaign'
            generate(path, ['didala'])
            tape = next((path / 'cases').glob('*.json'))
            tape.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'changed input tape'):
                load_campaign(path)

    def test_required_native_missing_rejects_run_and_check(self):
        from unittest.mock import patch
        from tools.sampling_matrix import run
        with tempfile.TemporaryDirectory() as temp:
            campaign = Path(temp) / 'campaign'
            manifest = generate(campaign, ['didala'], require_native=True)
            entry = manifest['cases'][0]
            case = json.loads((campaign / 'cases' / (entry['id'] + '.json')).read_text())
            self.assertIs(case['require_native'], True)
            output = Path(temp) / 'output'
            with patch('tools.sampling_matrix.execute_batch') as engine:
                with self.assertRaisesRegex(ValueError, entry['id'] + ': missing native evidence'):
                    run(campaign, output, Path('/unused/godot'), [entry['id']])
                engine.assert_not_called()
            with self.assertRaisesRegex(ValueError, 'missing native evidence'):
                require_full_coverage(campaign, output)
            self.assertFalse(output.exists())

    def test_native_requirement_cannot_be_stripped_from_tape(self):
        from tools.sampling_matrix import digest
        with tempfile.TemporaryDirectory() as temp:
            campaign = Path(temp) / 'campaign'
            manifest = generate(campaign, ['didala'], require_native=True)
            entry = manifest['cases'][0]
            path = campaign / 'cases' / (entry['id'] + '.json')
            case = json.loads(path.read_text())
            del case['require_native']
            path.write_text(json.dumps(case))
            # Updating only the tape digest cannot remove the manifest obligation.
            entry['sha256'] = digest(path)
            (campaign / 'matrix.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'changed input tape'):
                load_campaign(campaign)

    def test_zero_executions_cannot_pass(self):
        from tools.sampling_matrix import digest
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'campaign'
            generate(path, ['didala'])
            output = Path(temp) / 'run'
            output.mkdir()
            (output / 'report.json').write_text(json.dumps({
                'matrix_sha256': digest(path / 'matrix.json'), 'errors': [], 'results': []}))
            with self.assertRaisesRegex(ValueError, 'incomplete matrix'):
                require_full_coverage(path, output)


if __name__ == '__main__':
    unittest.main()
