import copy
import unittest
from analyze import load,HERE,startfight_windows


class IntervalTests(unittest.TestCase):
    def setUp(self):self.gate=load('r12_test',HERE.parent/'native-fight-r12/analyze.py')

    def fixture(self):
        data=['true,true,false,false,true,56','false,false,false,false,true,56','true,false,false','true,true,false','true,true,false','false,false,true,false,true,56']
        return [dict(kind=k,data=d) for k,d in zip(self.gate.KINDS,data)]

    def test_outside_menu_events_do_not_become_startfight(self):
        outside=dict(kind='menu-exit',data='false,false,false')
        windows=startfight_windows([outside]+self.fixture()+[outside],self.gate.validate_boundary)
        self.assertEqual(len(windows),1)
        self.assertFalse(windows[0]['shape']['oracle_accepted'])
        self.assertFalse(windows[0]['shape']['certified_global_tick'])

    def test_missing_nested_and_unmatched_interval_refused(self):
        events=self.fixture()
        for bad in [[],events[:-1],events[1:],events[:1]+events,events+events[-1:]]:
            with self.subTest(events=bad),self.assertRaises(ValueError):startfight_windows(bad,self.gate.validate_boundary)

    def test_menu_outcome_mismatch_is_not_shape_success(self):
        events=copy.deepcopy(self.fixture());events[3]['data']='true,false,false'
        with self.assertRaises(ValueError):startfight_windows(events,self.gate.validate_boundary)

    def test_interleaved_menu_call_is_ambiguous(self):
        events=self.fixture();events.insert(4,dict(kind='menu-exit',data='true,true,false'))
        with self.assertRaises(ValueError):startfight_windows(events,self.gate.validate_boundary)


if __name__=='__main__':unittest.main()
