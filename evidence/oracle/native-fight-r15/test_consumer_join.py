import copy
import unittest
from consumer_join import join


class ConsumerJoinTests(unittest.TestCase):
    def fixture(self,result=False):
        identity='/game/p1/mc/h,1,doAllAction'
        events=[('decision-installed','yihu-sprite16,/game/p1/mc/h'),('consumer-query-before',identity+',/game/p1/mc,f:1:0:0:0,false')]
        for site,value in ([(9,True),(10,False),(11,False),(12,False)] if result else [(9,False)]):
            events.append(('fight-key-return',f'yihu-decision-{site},74,{str(value).lower()},/game/p1/mc,false,false,false,4,f:1:0:0:0,f:1:0:0:0'))
        events.append(('consumer-predicate-result',identity+','+str(result).lower()))
        if result:
            events += [(kind,identity+',/game/p1/mc,f:1:0:0:0,false') for kind in ['consumer-goto-before','consumer-goto-after']]
        return [dict(seq=i,kind=k,data=d) for i,(k,d) in enumerate(events,1)]

    def test_true_and_false_shape_never_certify_os_or_tick(self):
        for value in [False,True]:
            r=join(self.fixture(value))
            self.assertEqual(r['validated_count'],1)
            for flag in ['oracle_accepted','certified_global_tick','os_input_join_proven']:self.assertFalse(r[flag])

    def test_true_missing_after_refused(self):
        r=join(self.fixture(True)[:-1]);self.assertEqual(r['validated_count'],0);self.assertEqual(r['refused_count'],1)

    def test_installation_inside_interval_refused(self):
        rows=self.fixture(False);rows.insert(2,dict(seq=2,kind='decision-installed',data='yihu-sprite16,/game/p1/mc/h2'))
        self.assertEqual(join(rows)['validated_count'],0)

    def test_interleaved_queries_are_not_joined(self):
        rows=self.fixture(False);rows.insert(2,copy.deepcopy(rows[1]))
        self.assertEqual(join(rows)['validated_count'],0)

    def test_query_owner_ai_pause_or_site_mismatch_refused(self):
        for a,b in [('/game/p1/mc,','/game/p2/mc,'),('false,false,false','true,false,false'),('false,false,false','false,true,false'),('yihu-decision-9','yihu-decision-10')]:
            rows=self.fixture(False);rows[2]['data']=rows[2]['data'].replace(a,b)
            with self.subTest(change=b):self.assertEqual(join(rows)['validated_count'],0)

    def test_reused_installation_and_serial_refused(self):
        rows=self.fixture(False);rows.insert(1,copy.deepcopy(rows[0]));self.assertEqual(join(rows)['validated_count'],0)
        rows=self.fixture(False);rows+=copy.deepcopy(rows[1:]);self.assertEqual(join(rows)['validated_count'],1)

    def test_true_result_requires_complete_short_circuit_chain(self):
        rows=self.fixture(True);rows.pop(4);self.assertEqual(join(rows)['validated_count'],0)

    def test_outside_key_not_associated(self):
        rows=self.fixture(False);rows.append(dict(seq=20,kind='fight-key-return',data='unrelated'))
        r=join(rows);self.assertEqual(len(r['intervals'][0]['keys']),1)


if __name__=='__main__':unittest.main()
