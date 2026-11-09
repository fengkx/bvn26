import json
import unittest
import tempfile
from pathlib import Path
from analyze import validate_rows, analyze
from build_observer import build, ROOT, patch_fighter, patch_clock, sources, CLOCK, DECISION, HERE


class ObserverTests(unittest.TestCase):
    def test_original_alias_and_short_circuit_preserved(self):
        original=sources('scripts/fighter/ichigo.json')
        patched, sites=patch_fighter(original)
        self.assertEqual(len(sites),39)
        restored=patched
        for site in sites:
            restored=restored.replace(f'_root.__m002FightKey(_parent,{site["argument"]},"{site["site"]}")',f'_parent.kis({site["argument"]})')
        self.assertEqual(restored,original[DECISION])
        self.assertIn('nornalhit',{s['function'] for s in sites})
        helper=(HERE/'observer.as').read_text()
        self.assertEqual(helper.count('owner.kis(code)'),1)
        self.assertNotIn('Key.isDown =',helper)

    def test_repository_output_refused_before_compiler(self):
        with self.assertRaisesRegex(ValueError,"temporary directory"):
            build(HERE/"missing.jar", ROOT/"output-forbidden", "m002-fixture-r05")

    def test_inventory_drift_refused(self):
        original=sources('scripts/fighter/ichigo.json')
        original[DECISION]=original[DECISION].replace('_parent.kis(', '_parent.other(',1)
        with self.assertRaises(ValueError):patch_fighter(original)

    def test_timer_preserves_original_body(self):
        source=sources('scripts/main.json')[CLOCK]
        patched=patch_clock(source)
        self.assertEqual(patched.replace('\n_root.__m002ClockOrdinal++;\n_root.__m002Clock("entry");','').replace('\n_root.__m002Clock("exit");',''),source)
        with self.assertRaises(ValueError):patch_clock(source.replace('time = function()','other = function()'))

    def fixture(self):
        events=[('boot','x'),('clock-entry','1,f:1:0:0:0,false,false'),('actor-state','p1'+',f:1:0:0:0'*9),('actor-state','p2'+',f:1:0:0:0'*9),('clock-exit','1,f:1:0:0:0,false,false'),('actor-state','p1'+',f:1:0:0:0'*9),('actor-state','p2'+',f:1:0:0:0'*9),('fight-key-return','ichigo-decision-1,74,true,/game/p1/mc,false,false,false,4,f:1:0:0:0,f:1:0:0:0')]
        events += [('game-state','entry'),('game-state','exit')]
        raw=''.join(f'M002|fixture|{i}|{i}|1|'+(f'game-{data}' if kind=='game-state' else 'between-game-callbacks')+f'|{kind}|{data}\n' for i,(kind,data) in enumerate(events,1)).encode()
        return raw,dict(run_id='fixture',fight_sites=[dict(site='ichigo-decision-1')])

    def test_synthetic_parser_success_is_not_tick_proof(self):
        raw,build=self.fixture()
        result=validate_rows(raw,build)
        self.assertFalse(result['certified_global_tick'])
        self.assertFalse(result['exact_initial_state'])

    def test_foreign_tag_gap_owner_site_timer_and_intro_refused(self):
        raw,build=self.fixture()
        variants=[raw.replace(b'fixture',b'foreign',1),raw.replace(b'|8|8|',b'|9|8|'),raw.replace(b'/game/p1/',b'/game/p2/'),raw.replace(b'ichigo-decision-1',b'intro-renderSkip-1'),raw.replace(b'clock-exit',b'other'),raw.replace(b'74,true',b'74,false'),raw.replace(b'|8|8|',b'|8|0|')]
        for bad in variants:
            with self.subTest(raw=bad),self.assertRaises(ValueError):validate_rows(bad,build)

    def test_wrong_build_and_reused_tag_refused(self):
        build_data=json.loads((HERE/'build.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            (directory/'session.json').write_text(json.dumps(dict(observer_build={})))
            with self.assertRaisesRegex(ValueError,'identity mismatch'):
                analyze(directory,HERE/'build.json')
            (directory/'session.json').write_text(json.dumps(dict(observer_build=build_data)))
            prefix=('M002|'+build_data['run_id']+'|').encode()
            for name in ['prelaunch','input-baseline','after']:
                (directory/f'flashlog.{name}.log').write_bytes(prefix)
            (directory/'tagged.log').write_bytes(prefix)
            with self.assertRaisesRegex(ValueError,'Tag reuse'):
                analyze(directory,HERE/'build.json')

    def test_no_live_receipt_refused(self):
        with self.assertRaisesRegex(ValueError,'No r05 live'):analyze(None,HERE/'build.json')


if __name__=='__main__':unittest.main()
