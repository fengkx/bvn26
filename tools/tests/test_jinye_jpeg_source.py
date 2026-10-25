"""Pin source-derived JPEG55 reconstruction before renderer experiments."""
import json
import unittest
from unittest.mock import patch
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.jinye_jpeg_source import source, decoded_planes, compare


class JinyeJpegSourceTests(unittest.TestCase):
    def test_source_planes_match_explicit_native_bitmap(self):
        evidence = ROOT/'evidence/importer-loud-fail/r220/jpeg'
        metadata, _, _, alpha = source()
        pixels, metadata['plane_sha256'] = decoded_planes(evidence/'analysis',alpha)
        report = compare(evidence/'native',metadata,pixels)
        stored = json.loads((evidence/'analysis/summary.json').read_text())
        self.assertEqual(json.loads(json.dumps(report)),stored)
        self.assertEqual(report['exact'],3680)
        self.assertEqual(report['max_channel_delta'],0)
        self.assertFalse(report['production_admitted'])

    def test_native_rows_and_source_alpha_fail_closed(self):
        evidence = ROOT/'evidence/importer-loud-fail/r220/jpeg'
        metadata, _, _, alpha = source()
        with self.assertRaises(AssertionError):
            decoded_planes(evidence/'analysis',alpha[:-1])
        pixels, metadata['plane_sha256'] = decoded_planes(evidence/'analysis',alpha)
        rows = events(evidence/'native')
        damaged = [list(row) for row in rows]
        damaged[1][1] = damaged[1][1].rsplit(',',1)[0]
        for readback in (rows[:-1],damaged):
            with patch('tools.probes.jinye_jpeg_source.events',return_value=readback):
                with self.assertRaises(AssertionError):
                    compare(evidence/'native',metadata,pixels)
