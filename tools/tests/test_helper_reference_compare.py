import json
import tempfile
import unittest
from pathlib import Path

from tools.probes.compare_helper_reference import compare


class HelperReferenceCompareTests(unittest.TestCase):
    def write_case(self, source, native):
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        events = root / 'events.jsonl'
        events.write_text('\n'.join(json.dumps(row) for row in source) + '\n')
        output = root / 'native.json'
        output.write_text(json.dumps(native))
        return directory, events, output

    def test_uses_fight_tick_and_maps_xscale_to_facing(self):
        source = [
            {'kind': 'helper_state', 'fight_tick': -1,
             'value': 'p1,99,f:1:1:0:0,f:1:1:0:0,f:1:1:0:0,false,undefined,undefined,undefined,undefined'},
            {'kind': 'helper_state', 'fight_tick': 0,
             'value': 'p1,2,300,-25,100,true,undefined,undefined,undefined,undefined,undefined'},
        ]
        native = [{'tick': 0, 'slot': 'p1', 'frame': 2, 'x': 300.0, 'y': -25.0,
                   'action': None, 'attacking': True, 'facing': 1}]
        directory, events, native_path = self.write_case(source, native)
        self.addCleanup(directory.cleanup)
        result = compare(events, native_path)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['source_rows'], 1)
        self.assertEqual(result['source_only_fields'], ['hits', 'atm1', 'atm2', 'atm3'])

    def test_does_not_skip_initial_active_helper_frame(self):
        source = [{'kind': 'helper_state', 'fight_tick': 0,
                   'value': 'p1,2,280,-25,100,true,undefined,undefined,undefined,undefined,undefined'}]
        native = [{'tick': 0, 'slot': 'p1', 'frame': 1, 'x': -200.0, 'y': -200.0,
                   'action': None, 'attacking': False, 'facing': 1}]
        directory, events, native_path = self.write_case(source, native)
        self.addCleanup(directory.cleanup)
        result = compare(events, native_path)
        self.assertEqual(result['status'], 'different')
        self.assertEqual(result['first_difference']['field'], 'frame')
        self.assertEqual(result['first_difference']['tick'], 0)
        self.assertEqual(result['first_difference']['source_raw_row']['frame'], 2)
        self.assertEqual(result['first_difference']['native_raw_row']['frame'], 1)


if __name__ == '__main__':
    unittest.main()
