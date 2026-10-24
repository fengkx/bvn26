import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from PIL import Image

from tools.probes.run_yulong_wrapper import fixture, validate_graph, compare

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'evidence/importer-loud-fail/r34/wrapper'


class YulongWrapperDiagnosticTests(unittest.TestCase):
    def test_complete_wrapper_exact_and_source_pinned(self):
        data = fixture()
        self.assertEqual(data, json.loads((EVIDENCE/'fixture.json').read_text()))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            for case in data['cases']:
                for tick in case['samples']:
                    name = f"{case['id']}-{tick:03d}.png"
                    shutil.copyfile(EVIDENCE/name, out/name)
            report = compare(data, out)
        self.assertEqual((report['exact'], report['images']), (4, 4))
        self.assertTrue(report['wrapper_passed'])
        self.assertFalse(report['production_admitted'])
        provenance = json.loads((EVIDENCE/'provenance.json').read_text())
        for path, digest in provenance['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)
        self.assertEqual(hashlib.sha256((EVIDENCE/'fixture.json').read_bytes()).hexdigest(), provenance['fixture_sha256'])
        for row in report['rows']:
            self.assertEqual(row['max_channel_delta'], [0, 0, 0, 0])

    def test_premult_input_keeps_admitted_interpolation(self):
        admitted = (ROOT/'godot/tests/bitmap_sampler_diagnostic.gdshader').read_text()
        prefix = admitted[:admitted.index('    // Existing references')]
        prefix = prefix.replace('uniform sampler2D parameters : filter_nearest;',
                                'uniform sampler2D parameters : filter_nearest;\nuniform sampler2D coverage_texture : filter_nearest;')
        candidate = (ROOT/'godot/tests/wrapper_bitmap_input.gdshader').read_text()
        self.assertTrue(candidate.startswith(prefix))

    def test_missing_duplicate_and_production_claim_reject(self):
        data = fixture()
        for cases in ([], data['cases'][:1], data['cases']+data['cases']):
            bad = copy.deepcopy(data)
            bad['cases'] = cases
            with self.assertRaises(ValueError):
                compare(bad, EVIDENCE)
        data['production_admitted'] = True
        with self.assertRaises(ValueError):
            compare(data, EVIDENCE)

    def test_unknown_semantics_and_fractional_domain_reject(self):
        data = fixture()
        original = json.loads((ROOT/data['cases'][0]['timeline']).read_text())
        for mutate in ('clip_actions', 'transform', 'filter', 'coverage', 'samples', 'frame_action'):
            cases = copy.deepcopy(data['cases'])
            timeline = copy.deepcopy(original)
            defs = {d['character_id']: d for d in timeline['definitions']}
            if mutate == 'clip_actions':
                defs[156]['first_frame_display_list'][0]['clip_actions'] = [{'event': 'load'}]
                defs[156]['display_list_frames'] = [defs[156]['first_frame_display_list']]
            elif mutate == 'transform':
                cases[0]['placement']['matrix']['rotateSkew0'] = 1
                defs[157]['first_frame_display_list'] = [cases[0]['placement']]
                defs[157]['display_list_frames'] = [[cases[0]['placement']]]
            elif mutate == 'filter':
                cases[0]['placement']['filters'][0]['innerGlow'] = True
                defs[157]['first_frame_display_list'] = [cases[0]['placement']]
                defs[157]['display_list_frames'] = [[cases[0]['placement']]]
            elif mutate == 'coverage':
                cases[0]['normalization']['y'] = 198.25
            elif mutate == 'samples':
                cases[0]['samples'] = []
            else:
                defs[156]['display_list_frame_events'] = [[{'stop': True}]]
            with self.assertRaises(ValueError, msg=mutate):
                validate_graph(data['leaf'], cases, timeline)

    def test_one_channel_delta_fails_whole_image_gate(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            for case in data['cases']:
                for tick in case['samples']:
                    name = f"{case['id']}-{tick:03d}.png"
                    image = Image.open(EVIDENCE/name).convert('RGBA')
                    if case['owner'] == 157 and tick == 0:
                        image.putpixel((0, 0), (97, 96, 96, 255))
                    image.save(out/name)
            report = compare(data, out)
            self.assertEqual(report['exact'], 3)
            self.assertFalse(report['wrapper_passed'])
            self.assertFalse(report['production_admitted'])
            self.assertEqual(report['rows'][0]['max_channel_delta'], [1, 0, 0, 0])
