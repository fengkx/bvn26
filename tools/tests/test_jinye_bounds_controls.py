"""Only valid outward ShapeBounds bits may differ from locked diagnostic tags."""
import unittest
from tools.probes.build_jinye_bounds_controls import controls,expand


class BoundsControls(unittest.TestCase):
    def test_preregistered_grid(self):
        f,tags=controls();self.assertEqual(len(f['cases']),26);self.assertEqual(len(tags),13)
        for shape in f['shapes']:
            raw=bytes.fromhex(shape['raw_tag_hex']);cid=shape['parsed']['shape']
            self.assertEqual(tags[0][cid],raw)
            for v in f['variants']:
                changed,proof=expand(raw,v['side'],v['amount'])
                self.assertEqual(changed,tags[v['id']][cid]);self.assertEqual(len(changed),len(raw))
                self.assertTrue(set(proof['changed_bits'])<=set(proof['allowed_changed_bits']))

    def test_only_metadata_changes(self):
        f,tags=controls()
        for c in f['cases']:
            original=tags[0][c['shape']];changed=tags[c['variant']][c['shape']];proof=c['bounds_patch']
            repaired=bytearray(changed)
            for bit in proof['allowed_changed_bits']:
                mask=1<<(7-bit%8);repaired[bit//8]=(repaired[bit//8]&~mask)|(original[bit//8]&mask)
            self.assertEqual(bytes(repaired),original)

    def test_shrink_rejected(self):
        f,_=controls();raw=bytes.fromhex(f['shapes'][0]['raw_tag_hex'])
        with self.assertRaises(AssertionError):expand(raw,0,-1)
        with self.assertRaises(AssertionError):expand(raw,4,1)
        with self.assertRaises(AssertionError):expand(raw,None,1)


if __name__=='__main__':unittest.main()
