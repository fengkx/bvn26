import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

from tools.sampling_bitmap import main, collect, decode_row, difference, godot_images, HEADER, WIDTH, HEIGHT
from tools.sampling_native import sha


class BitmapTests(unittest.TestCase):
    def rows(self):
        def event(kind, value):
            return f'AIREF|test|1|0|0|0|{kind}|{value}'
        return [event('bitmap_begin', HEADER)] + [
            event('bitmap_row', f'{y},ff123456:600;') for y in range(HEIGHT)
        ] + [event('bitmap_end', str(HEIGHT))]

    def test_argb_decode_and_exact_bytes(self):
        self.assertEqual(decode_row('ff123456:1;', 1), b'\x12\x34\x56\xff')
        images = collect(self.rows(), 'test', 0)
        self.assertEqual(len(images[0]), WIDTH*HEIGHT*4)
        self.assertTrue(difference(images[0], images[0])['exact'])

    def test_missing_duplicate_and_semantics_reject(self):
        rows = self.rows()
        for bad in [rows[:-1], rows[:7]+rows[8:], rows[:7]+[rows[6]]+rows[7:],
                    [rows[0].replace('RGBA8', 'BGRA8')]+rows[1:]]:
            with self.assertRaises(ValueError):
                collect(bad, 'test', 0)
        with self.assertRaises(ValueError):
            collect(rows, 'test', 1)

    def test_nonopaque_overflow_truncated_runs_reject(self):
        for row in ['7f123456:1;', 'ff123456:2;', 'ff123456:1', 'ff123456:0;']:
            with self.assertRaises(ValueError):
                decode_row(row, 1)

    def test_one_channel_one_byte_fails(self):
        expected = bytes((4, 5, 6, 255))
        actual = bytes((4, 6, 6, 255))
        result = difference(expected, actual, 1)
        self.assertFalse(result['exact'])
        self.assertEqual(result['different_channels'], 1)
        self.assertEqual(result['max_channel_delta'], 1)

    def test_godot_missing_changed_and_wrong_semantics_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            case = path/'case.json'
            case.write_text(json.dumps({'id': 'one', 'frames': 0}))
            image = path/'000.png'
            Image.new('RGBA', (WIDTH, HEIGHT), (1, 2, 3, 255)).save(image)
            manifest = {'case_id': 'one', 'case_sha256': sha(case), 'width': WIDTH,
                        'height': HEIGHT, 'phase': 'root-observer', 'format': 'RGBA8',
                        'background': 'opaque-black', 'production_admitted': False,
                        'native_parity_proven': False,
                        'runner_sha256': sha(Path('godot/tests/move_case_reference.gd')),
                        'images': [{'tick': 0, 'file': '000.png', 'sha256': sha(image)}]}
            meta = path/'bitmap.json'
            meta.write_text(json.dumps(manifest))
            self.assertEqual(len(godot_images(path, case)), 1)
            manifest['phase'] = 'post-frame'
            meta.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError): godot_images(path, case)
            manifest['phase'] = 'root-observer'
            manifest['images'] = []
            meta.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError): godot_images(path, case)
            manifest['images'] = [{'tick': 0, 'file': '000.png', 'sha256': sha(image)}]
            meta.write_text(json.dumps(manifest))
            image.write_bytes(b'changed')
            with self.assertRaises(ValueError): godot_images(path, case)
            image.unlink()
            with self.assertRaises(OSError): godot_images(path, case)

    def test_cli_byte_difference_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            case = path/'case.json'
            case.write_text('{}')
            receipt = path/'receipt.json'
            trace = path/'trace.log'
            trace.write_text('')
            receipt.write_text(json.dumps({'build': str(path), 'trace': str(trace)}))
            (path/'build.json').write_text(json.dumps({
                'sampling_bitmap': True, 'run_id': 'test', 'move_case': {'id': 'one', 'frames': 0}}))
            (path/'bitmap.json').write_text('{}')
            output = path/'result.json'
            argv = ['sampling_bitmap', '--case', str(case), '--receipt', str(receipt),
                    '--godot', str(path), '--output', str(output)]
            with patch('sys.argv', argv), patch('tools.sampling_bitmap.validate', return_value='fixture'), \
                    patch('tools.sampling_bitmap.collect', return_value=[bytes((0,0,0,255))]), \
                    patch('tools.sampling_bitmap.godot_images', return_value=[bytes((0,0,1,255))]), \
                    self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(json.loads(output.read_text())['exact_frames'], 0)


if __name__ == '__main__':
    unittest.main()
