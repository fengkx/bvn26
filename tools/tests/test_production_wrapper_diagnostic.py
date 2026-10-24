import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.probes.run_production_wrapper import analyze_stages, path_passed, validate_asset
from tools.probes.run_yulong_wrapper import fixture, compare

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'evidence/importer-loud-fail/r35/production-path'


class ProductionWrapperDiagnosticTests(unittest.TestCase):
    def test_actual_composition_mismatch_remains_loud(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for path in EVIDENCE.glob('*.png'):
                shutil.copyfile(path, output/path.name)
            report = compare(data, output)
        self.assertEqual((report['images'], report['exact']), (4, 0))
        self.assertFalse(report['wrapper_passed'])
        for row in report['rows']:
            self.assertEqual(row['different_pixels'], 114)
            self.assertEqual(row['max_channel_delta'], [1, 1, 1, 0])
            self.assertEqual(row['changed_channels'], [8, 113, 114, 0])
        stages = analyze_stages(data, EVIDENCE)
        self.assertFalse(path_passed(report, stages))
        self.assertFalse(report['production_admitted'])

    def test_png_and_bounded_buffers_match_prior_exact_path(self):
        data = fixture()
        validate_asset(data)
        stages = analyze_stages(data, EVIDENCE)
        self.assertEqual(stages['png_premultiplied_texels_exact'], 102)
        for stage in stages['stages']:
            self.assertEqual(stage['exact_pixels'], stage['pixels'])
        provenance = json.loads((EVIDENCE/'provenance.json').read_text())
        for path, digest in provenance['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)
        self.assertEqual(hashlib.sha256((EVIDENCE/'fixture.json').read_bytes()).hexdigest(), provenance['fixture_sha256'])
        self.assertEqual(hashlib.sha256((EVIDENCE/'texture-import.txt').read_bytes()).hexdigest(), provenance['texture_import_sha256'])

    def test_stage_success_cannot_override_final_pixel_failure(self):
        report = json.loads((EVIDENCE/'comparison.json').read_text())
        stages = json.loads((EVIDENCE/'stages.json').read_text())
        self.assertFalse(path_passed(report, stages))
        # Exercise both independent conditions with synthetic report fields only.
        report.update(wrapper_passed=True, exact=4)
        self.assertTrue(path_passed(report, stages))
        for field in ('png_premultiplied_texels_exact', 'stages', 'production_admitted'):
            bad = copy.deepcopy(stages)
            bad[field] = {'png_premultiplied_texels_exact': 101, 'stages': [], 'production_admitted': True}[field]
            self.assertFalse(path_passed(report, bad))
        report['production_admitted'] = True
        self.assertFalse(path_passed(report, stages))

    def test_missing_or_changed_buffer_observations_reject(self):
        data = fixture()
        records = json.loads((EVIDENCE/'buffers.json').read_text())
        for altered in ([], copy.deepcopy(records)):
            if altered:
                altered[0]['buffers'][0]['global_origin'] = [281, 197]
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                shutil.copyfile(EVIDENCE/'decoded.png', output/'decoded.png')
                (output/'buffers.json').write_text(json.dumps(altered))
                with self.assertRaises(ValueError):
                    analyze_stages(data, output)

    def test_sampler_interpolation_matches_admitted_shader(self):
        admitted = (ROOT/'godot/tests/bitmap_sampler_diagnostic.gdshader').read_text()
        bound = (ROOT/'godot/tests/production_bitmap_sampler.gdshader').read_text()
        # Only source decoding/binding and coverage differ; no fitted interpolation.
        a = admitted[admitted.index('    vec4 result;'):admitted.index('    // Existing references')]
        b = bound[bound.index('    vec4 result;'):bound.index('    COLOR =')]
        self.assertEqual(a.replace('p.b', 'metadata.b'), b)
