import copy
import unittest
from build_observer import r07,patch_fighter,HERE
from analyze import validate_consumer


class ConsumerTests(unittest.TestCase):
    def test_original_predicate_and_goto_restored_exactly(self):
        source=r07.patch_fighter(r07.sources('scripts/fighter/yihu.json'))[0]
        patched,changes=patch_fighter(source)
        restored=patched.removesuffix('\nvar __m002ConsumerSerial = 0;\n')
        for c in changes:restored=restored.replace(c['replacement'],c['original'],1)
        self.assertEqual(restored,source)
        self.assertEqual(patched.count('nornalhit()'),source.count('nornalhit()'))
        self.assertEqual(patched.count('gotoAndPlay('),source.count('gotoAndPlay('))
        self.assertNotIn('Key.isDown =',(HERE/'observer.as').read_text())
        self.assertIn('return result;', (HERE/'observer.as').read_text())

    def test_source_drift_refused(self):
        source=r07.patch_fighter(r07.sources('scripts/fighter/yihu.json'))[0]
        with self.assertRaises(ValueError):patch_fighter(source.replace('if(nornalhit())','if(other())',1))

    def fixture(self,result='true'):
        ids='/game/p1/mc/helper,1,doAllAction'
        return [dict(kind='consumer-query-before',data=ids+',/game/p1/mc,f:1:0:0:0,false'),dict(kind='consumer-predicate-result',data=ids+','+result)]+([dict(kind=k,data=ids+',/game/p1/mc,f:1:0:0:0,false') for k in ['consumer-goto-before','consumer-goto-after']] if result=='true' else [])

    def test_shape_never_certifies_os_join_or_global_tick(self):
        for result in ['true','false']:
            r=validate_consumer(self.fixture(result))
            self.assertFalse(r['certified_global_tick']);self.assertFalse(r['os_input_join_proven']);self.assertFalse(r['oracle_accepted'])

    def test_false_predicate_cannot_manufacture_goto(self):
        events=self.fixture();events[1]['data']=events[1]['data'].replace(',true',',false')
        with self.assertRaises(ValueError):validate_consumer(events)

    def test_missing_exit_and_wrong_owner_or_serial_refused(self):
        events=self.fixture()
        variants=[events[:-1],events[::-1]]
        for i in [1,2]:
            bad=copy.deepcopy(events);bad[i]['data']=bad[i]['data'].replace(',1,',',2,');variants.append(bad)
        bad=copy.deepcopy(events);bad[2]['data']=bad[2]['data'].replace(',/game/p1/mc,',',/game/p2/mc,');variants.append(bad)
        for bad in variants:
            with self.assertRaises(ValueError):validate_consumer(bad)

    def test_ai_branch_not_called_physical_consumption(self):
        events=self.fixture();events[0]['data']=events[0]['data'].removesuffix('false')+'true'
        with self.assertRaisesRegex(ValueError,'AI'):validate_consumer(events)


if __name__=='__main__':unittest.main()
