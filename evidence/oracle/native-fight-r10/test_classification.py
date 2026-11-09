import copy
import json
import unittest
from analyze import R09,r05,classify


class ClockClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=json.loads((R09/'build.json').read_text())
        cls.rows=r05.base.parse((R09/'run-01/tagged.log').read_bytes(),build['run_id'])

    def test_all_48_boundaries_and_raw_unknowns_retained(self):
        report=classify(self.rows)
        self.assertEqual(len(report['clock_boundaries']),48)
        incomplete=[r for r in report['clock_boundaries'] if not r['complete_fields']]
        self.assertEqual(len(incomplete),12)
        self.assertEqual({m['field'] for r in incomplete for m in r['missing']},{'hp'})
        self.assertEqual({m['raw_value'] for r in incomplete for m in r['missing']},{'undefined'})
        self.assertFalse(report['oracle_accepted'])

    def test_post_assignment_missing_hp_remains_incomplete(self):
        rows=copy.deepcopy(self.rows)
        after=next(i for i,r in enumerate(rows) if r['kind']=='chushi-hp-after')
        clock=next(i for i in range(after+3,len(rows)) if rows[i]['kind']=='clock-entry')
        fields=rows[clock+1]['data'].split(',');fields[5]='undefined';rows[clock+1]['data']=','.join(fields)
        report=classify(rows)
        self.assertEqual(report['post_assignment_incomplete'],1)
        self.assertFalse(report['oracle_accepted'])

    def test_missing_duplicate_or_reordered_hp_markers_refused(self):
        for mutation in ['missing','duplicate','reordered']:
            rows=copy.deepcopy(self.rows)
            before=next(i for i,r in enumerate(rows) if r['kind']=='chushi-hp-before')
            after=next(i for i,r in enumerate(rows) if r['kind']=='chushi-hp-after')
            if mutation=='missing':rows.pop(after)
            elif mutation=='duplicate':rows.append(copy.deepcopy(rows[before]))
            else:rows[before],rows[after]=rows[after],rows[before]
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):classify(rows)

    def test_incomplete_assignment_result_cannot_establish_phase(self):
        rows=copy.deepcopy(self.rows)
        i=next(i for i,r in enumerate(rows) if r['kind']=='chushi-hp-after')
        fields=rows[i+1]['data'].split(',');fields[5]='undefined';rows[i+1]['data']=','.join(fields)
        with self.assertRaisesRegex(ValueError,'HP after'):classify(rows)

    def test_timer_gap_and_missing_actor_refused(self):
        for mutation in ['gap','actor']:
            rows=copy.deepcopy(self.rows);i=next(i for i,r in enumerate(rows) if r['kind']=='clock-entry')
            if mutation=='gap':rows[i]['data']='2,'+rows[i]['data'].split(',',1)[1]
            else:rows.pop(i+1)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):classify(rows)

    def test_hp_assignment_not_relabelled_fight_start(self):
        report=classify(self.rows)
        self.assertLess(report['hp_after']['marker']['seq'],report['first_observed_unpaused']['seq'])
        self.assertEqual(report['hp_after']['marker']['data'].split(',')[1:3],['true','false'])
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])


if __name__=='__main__':unittest.main()
