"""Exact signed field patches must preserve all unrelated source bits."""
import struct
import unittest
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_jinye_sampling_modes import sampling_tag
from tools.probes.build_jinye_fill_translation_controls import translation_fields,changed_tag,controls


class JinyeFillTranslationControlsTests(unittest.TestCase):
    def shapes(self):
        return [(p,r) for c,p,r in source_tags(ROOT/'game/fighter/fz/jinye.swf') if c==2 and struct.unpack_from('<H',p)[0] in (56,57)]

    def test_signed_patch_changes_only_mode_and_selected_field(self):
        _,_,variants=controls()
        for payload,raw in self.shapes():
            for variant in variants:
                changed,metadata=changed_tag(payload,raw,variant['axis'],variant['delta'])
                self.assertTrue(set(metadata['changed_bits'])<=set(metadata['allowed_changed_bits']))
                self.assertEqual(len(changed),len(raw))
                self.assertEqual(metadata['before'][0],metadata['after'][0])
                for axis in (0,1):
                    delta=variant['delta'] if axis==variant['axis'] else 0
                    self.assertEqual(metadata['after'][1]['translations'][axis]['value'],metadata['before'][1]['translations'][axis]['value']+delta)
                if variant['axis'] is None:self.assertEqual(changed,sampling_tag(payload,raw,67)[0])

    def test_existing_signed_width_cannot_expand(self):
        payload,raw=next((p,r) for p,r in self.shapes() if struct.unpack_from('<H',p)[0]==57)
        self.assertEqual(translation_fields(payload)[1]['translations'][0]['width'],9)
        with self.assertRaises(AssertionError):changed_tag(payload,raw,0,22)

    def test_fill_and_draw_are_independent_controls(self):
        _,cases,variants=controls();self.assertEqual(len(cases),100);self.assertEqual(len(variants),13)
        self.assertEqual(sum(c['fill_variant']==0 for c in cases),52)
        for c in cases:
            self.assertFalse(c['fill_variant'] and c['draw_variant'])
            self.assertEqual(c['matrix'],next(b['matrix'] for b in cases if b['baseline_id']==c['baseline_id'] and b['fill_variant']==0 and b['draw_variant']==0))


if __name__=='__main__':unittest.main()
