import json
from pathlib import Path
import shutil
import tempfile
import unittest
from urllib.parse import unquote
from analyze import HERE,analyze


class ReceiptTests(unittest.TestCase):
    def test_rejected_prefix_retains_observed_hp_transition(self):
        report=analyze(HERE/'run-01')
        before,after=report['hp_boundaries']
        self.assertLess(before['marker']['seq'],after['marker']['seq'])
        self.assertEqual([unquote(a['data'].split(',')[5]) for a in before['actors']],['undefined','undefined'])
        self.assertEqual([unquote(a['data'].split(',')[5]) for a in after['actors']],[unquote(after['marker']['data'].split(',')[0])]*2)
        self.assertGreater(report['fight_key_positive'],0)
        self.assertFalse(report['structural_observations_admitted'])
        self.assertFalse(report['oracle_accepted'])
        self.assertEqual(report['structural_refusal'],'Incomplete actor state at clock boundary')

    def test_missing_post_goto_keeps_true_candidate_unjoined(self):
        report=analyze(HERE/'run-01')
        consumer=report['consumer_analysis']
        self.assertEqual(consumer['validated_predicates'],{'false':223})
        refused=[x for x in consumer['intervals'] if 'refusal' in x]
        self.assertEqual(len(refused),1)
        self.assertEqual(refused[0]['key_join_status'],'not-joined')
        self.assertNotIn('consumer-goto-after',[m['kind'] for m in refused[0]['markers']])
        self.assertFalse(report['certified_global_tick'])
        self.assertFalse(report['os_input_join_proven'])

    def test_raw_tag_selection_tampering_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            for name in ['session.json','flashlog.prelaunch.log','flashlog.input-baseline.log','flashlog.after.log','tagged.log']:
                shutil.copyfile(HERE/'run-01'/name,directory/name)
            raw=(directory/'tagged.log').read_bytes()
            (directory/'tagged.log').write_bytes(raw.split(b'\n',1)[1])
            with self.assertRaisesRegex(ValueError,'Raw/tag selection'):analyze(directory)

    def test_build_identity_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            session=json.loads((HERE/'run-01/session.json').read_text())
            session['observer_build']['run_id']='foreign'
            (directory/'session.json').write_text(json.dumps(session))
            with self.assertRaisesRegex(ValueError,'Build/session'):analyze(directory)


if __name__=='__main__':unittest.main()
