import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.probes.analyze_jinye_profile import append_row,baseline_label,verify_built_movie
from tools.probes.profile_native_cache import profile

class ProfileTests(unittest.TestCase):
    def test_baselines(self):
        self.assertEqual(baseline_label('direct_cached_regenerate'),'1-direct')
        self.assertEqual(baseline_label('local_uncached'),'0-local')
        with self.assertRaises(AssertionError):baseline_label('unknown')

    def test_strict_rows(self):
        for values in (['0','0'],['1','0','-16777216'],['0',str(1<<32),'-16777216']):
            with self.assertRaises(AssertionError):append_row({'size':[1,1],'pixels':[],'raw':[]},values)
        image={'size':[1,1],'pixels':[],'raw':[]};append_row(image,['0','0','-16777216'])
        self.assertEqual(image['pixels'],[[0,0,0,0]])

    def test_explicit_build_requires_identical_receipt_and_movie(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'game').mkdir();(root/'game/main.swf').write_bytes(b'original')
            receipt={'swf_sha256':hashlib.sha256(b'original').hexdigest(),'run_id':'pinned'}
            (root/'build.json').write_text(json.dumps(receipt))
            verify_built_movie(Path('/missing-archive-movie'),receipt,root)
            with self.assertRaises(AssertionError):verify_built_movie(root,{**receipt,'run_id':'other'},root)
            (root/'game/main.swf').write_bytes(b'changed')
            with self.assertRaises(AssertionError):verify_built_movie(root,receipt,root)

    def test_profile_canonicalizes_before_ownership_check(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);actual=root/'real';actual.mkdir();alias=root/'alias';alias.symlink_to(actual)
            with patch('tools.probes.profile_native_cache.preflight'),patch('tools.probes.profile_native_cache.matching_players',return_value={17}) as matching:
                with self.assertRaisesRegex(RuntimeError,'pre-existing'):profile(alias,root/'output',alias)
                self.assertEqual(matching.call_args.args,((actual/'game/main.swf').resolve(),actual.resolve()/'Contents/MacOS/Flash Player Debugger'))

if __name__=='__main__':unittest.main()
