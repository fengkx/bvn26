import tempfile
import unittest
from pathlib import Path

from tools.sampling_display import collect, enrich, source_timelines


class DisplayTests(unittest.TestCase):
    def event(self, kind, value=''):
        return f'AIREF|test|1|0|0|0|{kind}|{value}'

    def rows(self):
        return [self.event('display_begin'),
                self.event('display_camera', '800,600,noScale,TL,1,0,0,1,0,0,1,0,0,1,0,0'),
                self.event('display_node', '_level0.game,_level0,1,undefined,0,1,1,0,0,1,0,0,1,0,0,1,0,0,true,100,normal,false,none,0'),
                self.event('display_children', '_level0.game,0'),
                self.event('display_end', '1')]

    def test_explicit_empty_children_and_camera(self):
        sample = collect(self.rows(), 'test', 0)[0]
        self.assertEqual(sample['nodes']['_level0.game']['child_count'], 0)
        self.assertEqual(sample['camera']['stage_width'], 800)

    def test_missing_sample_camera_node_or_child_inventory_rejects(self):
        rows = self.rows()
        for index in range(len(rows)):
            with self.subTest(index=index), self.assertRaises((ValueError, KeyError)):
                collect(rows[:index] + rows[index+1:], 'test', 0)
        with self.assertRaises(ValueError):
            collect(rows, 'test', 1)

    def test_child_count_filter_count_and_duplicate_reject(self):
        for before, after in [('game,0', 'game,1'), ('none,0', 'none,1')]:
            with self.assertRaises(ValueError):
                collect([row.replace(before, after) for row in self.rows()], 'test', 0)
        rows = self.rows()
        with self.assertRaises(ValueError):
            collect(rows[:3]+[rows[2]]+rows[3:], 'test', 0)

    def test_unresolved_source_is_retained_as_gap(self):
        samples = collect(self.rows(), 'test', 0)
        gaps = enrich(samples, {})
        self.assertEqual(gaps[0]['reason'], 'unresolved runtime symbol')
        self.assertIn('_level0.game', samples[0]['nodes'])

    def test_source_move_retains_symbol_mask_and_filter_order(self):
        xml = '''<swf><tags>
        <item type="PlaceObject3Tag" depth="1" characterId="7" clipDepth="3">
          <surfaceFilterList><item type="BLURFILTER"/><item type="GLOWFILTER"/></surfaceFilterList>
        </item><item type="ShowFrameTag"/>
        <item type="PlaceObject2Tag" depth="1" placeFlagMove="true"><matrix translateX="20"/></item>
        <item type="ShowFrameTag"/></tags></swf>'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'source.xml'
            path.write_text(xml)
            frames, _ = source_timelines(path)
        record = frames[0][1][1]
        self.assertEqual(record['attributes']['characterId'], '7')
        self.assertEqual(record['attributes']['clipDepth'], '3')
        self.assertEqual([x['attributes']['type'] for x in record['fields']['surfaceFilterList']['children']],
                         ['BLURFILTER', 'GLOWFILTER'])


if __name__ == '__main__':
    unittest.main()
