import unittest
from tools.sampling_geometry import collect

SOURCE = 'game/fighter/didala.swf#DefineSprite_2/frame_1/DoAction.as'


class GeometryTests(unittest.TestCase):
    def event(self, tick, kind, value=''):
        return f'AIREF|test|1|0|{tick}|{tick}|{kind}|{value}'

    def box(self, tick=0, identity='1', source=SOURCE):
        return self.event(tick, 'geometry_box',
                          f'hurt,_level0.game.p1.mc.bdmn,{identity},{source},0,2,1,1,0,0,1,100,200,-2,-3,2,3')

    def test_explicit_empty_samples_are_valid(self):
        rows = [self.event(0, 'geometry_begin'), self.event(0, 'geometry_end', '0,0')]
        self.assertEqual(collect(rows, 'test', 0, {SOURCE})['samples'][0]['boxes'], [])

    def test_global_matrix_source_and_observed_lifetime(self):
        rows = []
        for tick in range(2):
            rows += [self.event(tick, 'geometry_begin'), self.box(tick), self.event(tick, 'geometry_end', '1,1')]
        result = collect(rows, 'test', 1, {SOURCE})
        self.assertEqual(result['samples'][0]['boxes'][0]['global_matrix'], [1,0,0,1,100,200])
        self.assertEqual(result['observed_lifetimes']['1']['last_observed_tick'], 1)

    def test_missing_sample_end_and_box_reject(self):
        rows = [self.event(0, 'geometry_begin'), self.box(), self.event(0, 'geometry_end', '1,1')]
        for bad, frames in ((rows, 1), (rows[:-1], 0), ([rows[0], rows[2]], 0), (rows + rows, 0)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                collect(bad, 'test', frames, {SOURCE})

    def test_duplicate_unknown_source_and_nonfinite_reject(self):
        for boxes in ([self.box(), self.box()], [self.box(source='unknown')],
                      [self.box().replace(',100,', ',NaN,')]):
            rows = [self.event(0, 'geometry_begin'), *boxes, self.event(0, 'geometry_end', f'{len(boxes)},1')]
            with self.subTest(boxes=boxes), self.assertRaises(ValueError):
                collect(rows, 'test', 0, {SOURCE})

    def test_probe_errors_never_become_empty_success(self):
        with self.assertRaisesRegex(ValueError, 'unbound'):
            collect([self.event(0, 'geometry_error', 'unbound:box')], 'test', 0, {SOURCE})


if __name__ == '__main__':
    unittest.main()
