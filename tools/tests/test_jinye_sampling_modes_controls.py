"""Sampling-mode countercontrols change exactly the parsed active fill byte."""
import struct
import unittest
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_jinye_sampling_modes import active_fill_offset,sampling_tag,controls,source_pixel
from tools.probes.build_jinye_affine_controls import controls as old_controls


class JinyeSamplingModeControlsTests(unittest.TestCase):
    def test_only_active_bitmap_type_byte_changes(self):
        shapes=[(p,r) for code,p,r in source_tags(ROOT/'game/fighter/fz/jinye.swf') if code==2 and struct.unpack_from('<H',p)[0] in (56,57)]
        self.assertEqual(len(shapes),2)
        for payload,raw in shapes:
            offset,styles=active_fill_offset(payload)
            self.assertEqual([s['bitmap'] for s in styles],[65535,55])
            self.assertEqual(sampling_tag(payload,raw,65)[0],raw)
            changed,metadata=sampling_tag(payload,raw,67)
            self.assertEqual([i for i,(a,b) in enumerate(zip(raw,changed)) if a!=b],[metadata['tag_offset']])
            self.assertEqual(raw[metadata['tag_offset']],65);self.assertEqual(changed[metadata['tag_offset']],67)
            invalid=bytearray(payload);invalid[offset+1]=54
            with self.assertRaises(AssertionError):active_fill_offset(invalid)

    def test_coordinate_source_and_geometry_preserved(self):
        _,old=old_controls();_,cases,clips=controls()
        self.assertEqual(len(cases),4);self.assertEqual(clips,[None,[46,0,1,96],[47,0,1,96],[48,0,1,96]])
        for c in cases:
            for field in ('shape','fill','mask','matrix','outer','draw'):
                self.assertEqual(c[field],old[c['base_h']][field]);self.assertEqual(c[field],old[c['base_v']][field])
        self.assertEqual(source_pixel(91,39),[182,234,73,255])


if __name__=='__main__':unittest.main()
