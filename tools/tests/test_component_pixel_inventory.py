"""Inventory diagnostics preserve distinct channels and fail on missing evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    from PIL import Image
except ImportError:
    Image = None


@unittest.skipIf(Image is None, 'Pillow is required for image inventory')
class ComponentPixelInventoryTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('pixel_inventory',
            Path(__file__).resolve().parents[1]/'probes/inventory_component_pixels.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for path in ['components/sample','godot/sample','comparisons/sample']:
            (self.root/path).mkdir(parents=True)
        (self.root/'source.swf').write_bytes(b'locked')
        case = {'id':'sample','source':{'path':'source.swf','sha256':hashlib.sha256(b'locked').hexdigest()},
                'owner':4,'source_frame':7,'placement':{'depth':2},'symbol':9,'samples':[0]}
        (self.root/'components/sample/cases.json').write_text(json.dumps([case]))
        (self.root/'godot/sample/clocks.json').write_text(json.dumps([{'path':'sample','tick':0,'frame':1}]))
        Image.new('RGB',(1,1),(10,20,30)).save(self.root/'comparisons/sample/sample-000.native.png')
        Image.new('RGB',(1,1),(11,20,28)).save(self.root/'godot/sample/sample-000.png')

    def test_distinct_channels_and_source_location(self):
        with patch.object(self.module,'ROOT',self.root):
            result = self.module.inventory(self.root)
        self.assertEqual(result['exact'],0)
        row, = result['rows']
        self.assertEqual(row['different_channels'],{'R':1,'G':0,'B':1})
        self.assertEqual(row['max_channel_delta'],{'R':1,'G':0,'B':2})
        self.assertEqual((row['owner_sprite'],row['placement_frame'],row['clip']),(4,7,9))
        self.assertEqual(row['worst_samples'][0]['native_rgb'],[10,20,30])

    def test_missing_native_or_changed_source_is_not_green(self):
        with patch.object(self.module,'ROOT',self.root):
            (self.root/'source.swf').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Source hash mismatch'):
                self.module.inventory(self.root)
            (self.root/'source.swf').write_bytes(b'locked')
            (self.root/'comparisons/sample/sample-000.native.png').unlink()
            with self.assertRaises(FileNotFoundError):
                self.module.inventory(self.root)
