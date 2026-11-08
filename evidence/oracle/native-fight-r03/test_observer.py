import json
from pathlib import Path
import unittest
from analyze import parse
from build_observer import patch_sources, ROOT, BOOT, GAME, MUSIC, tags


class ObserverTests(unittest.TestCase):
    def test_rejects_foreign_duplicate_and_missing_boot(self):
        for raw in [b'M002|other|1|0|0|boot|boot|x\n',b'M002|run|1|0|0|boot|boot|x\nM002|run|1|1|0|boot|key-return|1,true\n',b'M002|run|1|0|0|boot|key-return|1,true\n']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse(raw,'run')

    def test_local_ordinal_does_not_require_global_tick(self):
        rows=parse(b'M002|run|1|700|0|before-game-callback|boot|x\nM002|run|2|720|0|before-game-callback|random-return|f:1:-1:33554432:0\n','run')
        self.assertEqual(rows[1]['ordinal'],0)
        self.assertEqual(rows[1]['timer_ms'],720)

    def test_source_boundaries_are_unique_and_fail_on_change(self):
        sources={s['path']:s['source'] for s in json.loads((ROOT/'scripts/main.json').read_text())['scripts']}
        result=patch_sources(sources,'m002-test-fixture')
        self.assertEqual(set(result),{BOOT,GAME,MUSIC})
        self.assertTrue(result[BOOT].startswith(sources[BOOT]))
        # Original control-flow operations must survive the observer insertion unchanged.
        for op in ['gotoAndPlay(', 'gotoAndStop(', 'clearInterval(', 'setInterval(']:
            self.assertEqual(result[GAME].count(op),sources[GAME].count(op))
        sources[GAME]=sources[GAME].replace('onEnterFrame = function()', 'different = function()')
        with self.assertRaises(ValueError):patch_sources(sources,'m002-test-fixture')

    def test_namespace_collision_fails_before_build(self):
        with self.assertRaisesRegex(ValueError,'collision'):
            patch_sources({'any':'__m002'},'m002-test-fixture')

    def test_run_tag_cannot_inject_source(self):
        with self.assertRaises(ValueError):patch_sources({},'bad";code')


if __name__ == '__main__':unittest.main()
