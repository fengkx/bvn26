import struct
import tempfile
from pathlib import Path
import unittest
from tools.probes.audit_affine_static_callers import verify_call, profile_counts


class StaticCallerTests(unittest.TestCase):
    def test_signed_relative_target(self):
        verify_call(b'\xe8'+struct.pack('<i',-10),100,95)
        with self.assertRaises(ValueError):
            verify_call(b'\xe8'+struct.pack('<i',-10),100,96)

    def test_module_relative_pc_ignores_aslr_base(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sample.txt'
            path.write_text('2 ???  (in Flash Player Debugger) load address 0xabcdef000 + 0x158208\nTotal number in stack\n9 ???  (in Flash Player Debugger) load address 0xabcdef000 + 0x158208\n')
            self.assertEqual(dict(profile_counts(path)),{0x100158208:2})

    def test_unrecognized_profile_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sample.txt';path.write_text('no profile PCs')
            with self.assertRaises(ValueError):profile_counts(path)


if __name__ == '__main__':
    unittest.main()
