"""Source-backed negatives for the unresolved, observed AImain frame-zero family."""
import copy
import gzip
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from urllib.parse import unquote

from tools.sampling_display import collect, enrich, source_timelines
from tools.sampling_native import sha

ROOT = Path(__file__).resolve().parents[2]


class DisplaySourceFrameDiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.xml = Path(cls.temp.name) / 'fighter-lee.xml'
        base = ROOT / 'evidence/sampling-upgrade/s86'
        with tarfile.open(base / 'lee-source-export.tar.gz') as archive:
            cls.xml.write_bytes(archive.extractfile('fighter-lee.xml').read())
        exports = json.loads((base / 'source-exports.json').read_text())
        assert sha(cls.xml) == exports['game/fighter/lee.swf']['xml_sha256']
        cls.frames, _ = source_timelines(cls.xml)
        cls.retained = json.loads(gzip.decompress((base / 'display.json.gz').read_bytes()))

    def sample(self, frame=0):
        nodes = self.retained['samples'][0]['nodes']
        parent_path = '_level0.game.p1.mc'
        child_path = parent_path + '.AImain'
        selected = copy.deepcopy({p: nodes[p] for p in (parent_path, child_path)})
        for node in selected.values():
            for key in ('symbol', 'source_swf', 'authored_children'):
                node.pop(key, None)
        selected[child_path]['frame'] = frame
        return [{'tick': 0, 'nodes': selected}]

    def test_authored_placement_and_frame_scripts_do_not_define_frame_zero(self):
        placement = self.frames[518][0][1]
        self.assertEqual(placement['attributes']['name'], 'AImain')
        self.assertEqual(placement['attributes']['characterId'], '3')
        self.assertEqual(placement['placement_frame'], 1)
        self.assertEqual(len(self.frames[3]), 2)
        self.assertEqual(self.frames[3][0], {})
        self.assertTrue(self.frames[3][1])
        bundle = json.loads((ROOT / 'scripts/fighter/lee.json').read_text())
        scripts = {s['path']: s['source'] for s in bundle['scripts']}
        self.assertEqual(scripts['DefineSprite_3/frame_1/DoAction.as'].strip(), 'stop();')
        self.assertNotIn('DefineSprite_3/frame_2/DoAction.as', scripts)
        self.assertIn('AImain.unloadMovie();', scripts['DefineSprite_518/frame_1/DoAction.as'])

    def test_zero_and_out_of_range_frames_remain_missing_not_aliased(self):
        for frame in (0, 3):
            with self.subTest(frame=frame):
                samples = self.sample(frame)
                gaps = enrich(samples, {'game/fighter/lee.swf': self.xml})
                node = samples[0]['nodes']['_level0.game.p1.mc.AImain']
                self.assertEqual(node['symbol'], 3)
                self.assertEqual(node['frame'], frame)
                self.assertNotIn('authored_children', node)
                self.assertIn({'tick': 0, 'path': '_level0.game.p1.mc.AImain',
                               'reason': 'missing source frame'}, gaps)

    def test_frame_two_still_requires_authored_sensor_children(self):
        gaps = enrich(self.sample(2), {'game/fighter/lee.swf': self.xml})
        missing = [g for g in gaps if g['path'].endswith('.AImain')]
        self.assertEqual({g['depth'] for g in missing}, set(self.frames[3][1]))
        self.assertTrue(all(g['reason'] == 'authored MovieClip absent from observed hierarchy' for g in missing))

    def test_all_five_raw_captures_retain_the_zero_frame_nodes(self):
        for slice_id in ('s86', 's93', 's100', 's248', 's249'):
            with self.subTest(slice=slice_id):
                base = ROOT / 'evidence/sampling-upgrade' / slice_id
                metadata = json.loads((base / 'native-build.json').read_text())
                lines = gzip.decompress((base / 'native-capture.log.gz').read_bytes()).decode().splitlines()
                samples = collect(lines, metadata['run_id'], 60)
                for actor in ('p1', 'p2'):
                    nodes = [s['nodes'][f'_level0.game.{actor}.mc.AImain'] for s in samples]
                    self.assertEqual(len(nodes), 61)
                    self.assertEqual({n['frame'] for n in nodes}, {0})
                    self.assertEqual({n['source_script'] for n in nodes}, {'undefined'})
                    self.assertEqual({n['child_count'] for n in nodes}, {0})
                    self.assertEqual(len({n['instance_id'] for n in nodes}), 1)
                removed = [line for line in lines if '|60|display_node|_level0.game.p1.mc.AImain,' not in unquote(line)]
                self.assertLess(len(removed), len(lines))
                with self.assertRaises((ValueError, KeyError)):
                    collect(removed, metadata['run_id'], 60)


if __name__ == '__main__':
    unittest.main()
