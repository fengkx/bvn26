"""The s64 placement gets a stamp without inventing a child frame action."""
import hashlib
import json
from pathlib import Path
import tarfile
import unittest
import xml.etree.ElementTree as ET

from tools.probes import deidara_atm1_observer as observer
from tools.probes.build_ai_reference import build

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / 'evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json'


class Atm1LoadStampTests(unittest.TestCase):
    def test_exact_source_body_preserved_and_stamp_inside_load(self):
        bundle = json.loads((ROOT / 'scripts/fighter/fz/woailuo.json').read_text())
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == observer.LOAD_PATH)
        old = observer.instrument_load(source, source, 'fighter/fz/woailuo', observer.LOAD_PATH)
        new = observer.instrument_load(source, source, 'fighter/fz/woailuo', observer.LOAD_PATH, stamp=True)
        stamp = f'\n_root.aiGeoStamp(this,"{observer.LOAD_SOURCE}");\n'
        self.assertEqual(new.count(stamp), 1)
        self.assertEqual(new.replace(stamp, ''), old)
        self.assertLess(new.index(stamp), new.index('"load_after"'))
        self.assertGreater(new.index(stamp), new.index('_X ='))
        self.assertEqual(observer.instrument_load('other', 'other', 'fighter/fz/kon', observer.LOAD_PATH, stamp=True), 'other')
        self.assertEqual(observer.instrument_load('stop();', 'stop();', 'fighter/fz/woailuo', 'DefineSprite_48/frame_33/DoAction.as', stamp=True), 'stop();')
        with self.assertRaises(ValueError):
            observer.instrument_load(source + ' ', source, 'fighter/fz/woailuo', observer.LOAD_PATH, stamp=True)

    def test_locked_placement_and_action_inventory(self):
        binding = json.loads((ROOT / 'evidence/sampling-upgrade/s246/source-binding.json').read_text())
        for path, key in ((binding['swf'], 'swf_sha256'), (binding['script_bundle'], 'script_bundle_sha256')):
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), binding[key])
        with tarfile.open(ROOT / binding['xml_archive']) as archive:
            raw = archive.extractfile(binding['xml_archive_member']).read()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), binding['xml_sha256'])
        root = ET.fromstring(raw)
        tags = root.find('tags')
        frame = 1
        placements = []
        for tag in tags:
            if tag.get('type') == 'ShowFrameTag':
                frame += 1
            if tag.get('name') == 'atm1':
                placements.append((frame, tag.get('characterId'), tag.get('depth'), tag.get('placeFlagMove')))
        self.assertEqual(placements, [(44, '48', '2', 'false')])
        sprite = next(t for t in tags if t.get('type') == 'DefineSpriteTag' and t.get('spriteId') == '48')
        frame = 1
        actions = []
        for tag in sprite.find('subTags'):
            if tag.get('type') == 'ShowFrameTag':
                frame += 1
            if tag.get('type') == 'DoActionTag':
                actions.append(frame)
        self.assertEqual(actions, [33])

    def test_wrong_configuration_rejected_before_build(self):
        config = dict(ffdec=Path('/unused'), output=Path('/unused'), run_id='test', frames=60,
                      move_case=CASE, p1_character='迪达拉', p2_character='一护',
                      p1_helper='我爱罗', p2_helper='魂', deidara_atm1_load_stamp=True,
                      profile='diagnostic', diagnostic_auto_start=True,
                      diagnostic_key_injection=True, diagnostic_trace_hooks=True)
        for override in ({'frames': 61}, {'p1_helper': '魂'}, {'p2_character': '鸣人'},
                         {'sampling_display': True}, {'sampling_bitmap': True},
                         {'dynamic_move_case': True}, {'sampling_callsite': True}):
            with self.subTest(override=override), self.assertRaisesRegex(ValueError, 'exclusive s64'):
                build(**(config | override))


class NativeLoadStampProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gzip
        import importlib.util
        path = ROOT / 'evidence/sampling-upgrade/s251'
        spec = importlib.util.spec_from_file_location('s251_proof', path / 'verify_lifetime.py')
        cls.proof = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.proof)
        cls.lines = gzip.open(path / 'native-capture.log.gz', 'rt').read().splitlines()
        cls.metadata = json.loads((path / 'native-build.json').read_text())

    def test_native_load_stamp_and_remaining_gate_obligations(self):
        report = self.proof.prove(self.lines, self.metadata)
        self.assertTrue(report['stamp_binding_complete'])
        self.assertEqual(report['geometry_samples'], 61)
        self.assertEqual(report['geometry_boxes'], 241)
        self.assertEqual(report['full_geometry_missing_receivers'], [{'tick': 11, 'slot': 'p1'}, {'tick': 41, 'slot': 'p1'}])
        self.assertFalse(report['native_parity_proven'])
        self.assertFalse(report['production_admitted'])

    def test_each_missing_boundary_and_geometry_box_rejects(self):
        for row in self.lines:
            if '|atm1_provenance|' in row or ('|geometry_box|' in row and '.p1fz.atm1,' in row):
                with self.subTest(row=row), self.assertRaises(ValueError):
                    self.proof.prove([line for line in self.lines if line != row], self.metadata)

    def test_changed_source_identity_birth_and_duplicate_rejects(self):
        row = next(r for r in self.lines if '|atm1_provenance|load_after,' in r)
        for index, value in ((1, 'wrong-source'), (7, '999'), (8, 'undefined'), (9, '0')):
            parts = row.split('|', 7); payload = parts[7].split(','); payload[index] = value
            parts[7] = ','.join(payload)
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.proof.prove([('|'.join(parts) if r == row else r) for r in self.lines], self.metadata)
        with self.assertRaises(ValueError):
            self.proof.prove(self.lines + [row], self.metadata)

    def test_old_unbound_geometry_still_rejects(self):
        import gzip
        from tools.sampling_geometry import collect
        for name in ('s64', 's246'):
            rows = gzip.open(ROOT / 'evidence/sampling-upgrade' / name / 'native-capture.log.gz', 'rt').read().splitlines()
            sources = {r.split('|', 7)[7].split(',')[3] for r in rows if '|geometry_box|' in r}
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'unbound'):
                collect(rows, rows[0].split('|')[1], 60, sources)


if __name__ == '__main__':
    unittest.main()
