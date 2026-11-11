"""An observed path/order must never become a dispatch or lifetime witness."""
import gzip
import json
import unittest
from analyze import HERE, LIVE, FLAGS, classify, replay

class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (LIVE / 'run-01/combined.log').read_bytes()
        cls.tag = json.loads((LIVE / 'build.json').read_text())['run_id']

    def refused(self, result):
        for flag in FLAGS:
            self.assertIs(result[flag], False)
        for row in result['targets']:
            for flag in ['initiating_call_join_proven', 'helper_lifetime_proven',
                         'removal_edge_proven', 'native_return_proven']:
                self.assertIs(row[flag], False)
            self.assertEqual(row['cause'], 'unproved')

    def test_actual_target_has_one_candidate_but_no_join(self):
        r = replay(); self.refused(r)
        t = r['targets'][0]
        self.assertEqual((t['preceding_root_seq'], t['following_root_seq']), (6932, 6933))
        self.assertEqual(len(t['source_prefix_candidates']), 1)
        self.assertEqual(t['source_prefix_candidates'][0]['serial'], '127')
        paths = {x['helper_path']: x for x in t['observed_installation_paths']}
        old = paths['/game/p1/mc/instance2915']
        self.assertEqual((old['seq'], old['query_count'], old['last_exact_path_root_seq']), (4498, 127, 6925))
        self.assertFalse(old['termination_observed'])
        self.assertEqual(r['structural_refusal'], 'Incomplete actor state at clock boundary')

    def test_other_owner_does_not_inherit_candidate(self):
        target = ('M002TARGET|' + self.tag + '|yihu638-frame174|').encode()
        raw = self.raw.replace(target + b'%2Fgame%2Fp1%2Fmc', target + b'%2Fgame%2Fp2%2Fmc')
        result = classify(raw, self.tag); self.refused(result)
        self.assertEqual(result['targets'][0]['source_prefix_candidates'], [])

    def test_adjacency_cannot_create_identity(self):
        lines = self.raw.splitlines()
        target = next(x for x in lines if x.startswith(b'M002TARGET|'))
        lines.remove(target)
        index = next(i for i,x in enumerate(lines) if x.startswith(b'M002LITERAL|'))
        lines.insert(index + 1, target)
        result = classify(b'\n'.join(lines) + b'\n', self.tag); self.refused(result)
        self.assertEqual(result['targets'][0]['preceding_root_seq'], 6925)

    def test_repeated_target_is_not_unique_return(self):
        lines = self.raw.splitlines(); target = next(x for x in lines if x.startswith(b'M002TARGET|'))
        result = classify(self.raw + target + b'\n', self.tag); self.refused(result)
        self.assertEqual(len(result['targets']), 2)

    def test_foreign_target_refused(self):
        with self.assertRaises(ValueError):
            classify(self.raw.replace(('M002TARGET|' + self.tag).encode(), b'M002TARGET|foreign'), self.tag)

    def test_missing_prefix_does_not_create_join(self):
        raw = self.raw.replace(b'|continuation-prep|', b'|unobserved-prep|')
        result = classify(raw, self.tag); self.refused(result)
        self.assertEqual(result['targets'][0]['source_prefix_candidates'], [])

    def test_shared_sprite_has_multiple_parent_call_sites(self):
        sites = json.loads((HERE / 'dispatch-source-sites.json').read_text())
        for parent in ('638', '1672'):
            self.assertIn('DefineSprite_' + parent + '/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as', sites)

    def test_receipt_matched_target_bytecode_has_no_helper_token(self):
        code = gzip.decompress((HERE / 'target.pcode.gz').read_bytes()).decode()
        self.assertIn('M002TARGET|' + self.tag + '|yihu638-frame174|', code)
        self.assertIn('"_target"', code)
        self.assertIn('"_currentframe"', code)
        for absent in ('instance2915', '__m002Call', 'getDepth', 'CallMethod'):
            self.assertNotIn(absent, code)
        self.assertTrue(code.endswith('Trace\r\nPush "动作"\r\nPush 1\r\nSetVariable\r\n'))
