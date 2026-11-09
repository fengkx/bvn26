import copy
import json
import unittest
from analyze import R09,r10,classify


class FightSubsetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=json.loads((R09/'build.json').read_text())
        cls.rows=r10.r05.base.parse((R09/'run-01/tagged.log').read_bytes(),build['run_id'])

    def test_first_subset_is_not_exact_start_or_admission(self):
        r=classify(self.rows)
        self.assertEqual(r['first_observed_subset']['marker']['seq'],3092)
        self.assertEqual(r['preceding_game_entry']['marker']['seq'],3074)
        self.assertFalse(r['exact_fight_start_proven'])
        self.assertFalse(r['full_fight_readiness_proven'])
        self.assertFalse(r['oracle_accepted'])
        self.assertEqual(len(r['clock_boundaries']),48)

    def test_later_pause_not_promoted_by_first_subset(self):
        r=classify(self.rows)
        later=[b for b in r['clock_boundaries'] if b['classification']=='post-hp-complete-paused' and b['relation_to_first_subset_checkpoint']=='at-or-after']
        self.assertEqual([b['boundary']['seq'] for b in later],[3920,3923])
        self.assertTrue(all(not b['timer_readiness_proven'] for b in r['clock_boundaries']))

    def test_unpaused_without_loading_flag_cannot_satisfy_subset(self):
        rows=copy.deepcopy(self.rows)
        for row in rows:
            if row['kind']=='game-state':
                fields=row['data'].split(',');fields[4]='false';row['data']=','.join(fields)
        r=classify(rows)
        self.assertIsNone(r['first_observed_subset'])
        self.assertEqual(r['subset_candidate_count'],0)

    def test_missing_actor_field_defers_candidate_without_filling(self):
        rows=copy.deepcopy(self.rows);i=next(i for i,r in enumerate(rows) if r['seq']==3092)
        fields=rows[i+1]['data'].split(',');fields[5]='undefined';rows[i+1]['data']=','.join(fields)
        r=classify(rows)
        self.assertGreater(r['first_observed_subset']['marker']['seq'],3092)
        failed=next(c for c in r['game_entries'] if c['marker']['seq']==3092)
        self.assertFalse(failed['conditions']['actor_fields_complete'])
        self.assertFalse(failed['observed_subset_satisfied'])

    def test_missing_ready_or_hp_marker_refused(self):
        for kind in ['ready-play-before','chushi-hp-after']:
            rows=[r for r in self.rows if r['kind']!=kind]
            with self.subTest(kind=kind),self.assertRaises(ValueError):classify(rows)

    def test_unknown_boolean_is_not_false(self):
        rows=copy.deepcopy(self.rows);row=next(r for r in rows if r['seq']==3092)
        fields=row['data'].split(',');fields[2]='undefined';row['data']=','.join(fields)
        with self.assertRaisesRegex(ValueError,'Malformed'):classify(rows)

    def test_post_hp_incomplete_timer_keeps_its_own_class(self):
        rows=copy.deepcopy(self.rows);i=next(i for i,r in enumerate(rows) if r['kind']=='clock-entry' and r['seq']>1145)
        fields=rows[i+1]['data'].split(',');fields[5]='undefined';rows[i+1]['data']=','.join(fields)
        r=classify(rows)
        self.assertEqual(r['timer_counts']['post-hp-incomplete'],1)
        self.assertFalse(r['oracle_accepted'])


if __name__=='__main__':unittest.main()
