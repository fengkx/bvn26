import copy
import unittest
import analyze
import build_observer as builder


class ContinuationTests(unittest.TestCase):
    def fixture(self):
        q = '/game/p1/mc/helper,1,doAllAction,/game/p1/mc,frame,false'
        data = [('decision-installed', 'yihu-sprite16,/game/p1/mc/helper'), ('consumer-query-before', q)]
        data += [('fight-key-return', f'yihu-decision-{s},74,{v},/game/p1/mc,false,false,false,3,x,y') for s, v in zip(range(9,13), ['true','false','false','false'])]
        data += [('consumer-predicate-result','/game/p1/mc/helper,1,doAllAction,true'), ('consumer-goto-before',q), ('continuation-prep','tag,/game/p1/mc/helper,1,doAllAction'), ('continuation-breadcrumb','tag,/game/p1/mc/helper,1,doAllAction'), ('consumer-goto-after',q)]
        return [dict(seq=i,kind=k,data=d) for i,(k,d) in enumerate(data,1)]

    def test_matched_with_and_without_dynamic_after(self):
        for rows in [self.fixture(), self.fixture()[:-1]]:
            result = analyze.classify(rows,'tag')
            self.assertEqual(result['outcomes'][0]['classification'],'matched')
            for flag in analyze.FLAGS:
                self.assertIs(result[flag],False)
        self.assertEqual(analyze.classify(self.fixture()[:-1],'tag')['outcomes'][0]['dynamic_after'],'absent-or-unmatched')

    def test_do_stand_pairing(self):
        rows=self.fixture()
        for row in rows:row["data"]=row["data"].replace("doAllAction","doStand")
        self.assertEqual(analyze.classify(rows,"tag")["outcomes"][0]["classification"],"matched")

    def test_missing_and_orphan(self):
        self.assertEqual(analyze.classify(self.fixture()[:-2],'tag')['outcomes'][0]['classification'],'prep-without-breadcrumb')
        self.assertEqual(analyze.classify([self.fixture()[-2]],'tag')['outcomes'][0]['classification'],'breadcrumb-without-prep')

    def test_interleaved_reinstall_duplicate_and_wrong_identity(self):
        for mode in ['interleave','reinstall','duplicate','wrong','foreign']:
            rows = self.fixture()
            if mode in ('interleave','reinstall'):
                rows.insert(-2,dict(seq=9,kind='decision-installed' if mode=='reinstall' else 'game-state',data='unrelated'))
            elif mode=='duplicate': rows.insert(-1,copy.deepcopy(rows[-2]))
            elif mode=='wrong': rows[-2]['data']=rows[-2]['data'].replace('helper','other')
            else: rows[-3]['data']=rows[-3]['data'].replace('tag,','foreign,')
            with self.subTest(mode=mode):
                self.assertFalse(any(x['source_continuation_observed'] for x in analyze.classify(rows,'tag')['outcomes']))

    def test_missing_predicate_and_ai_refused(self):
        for index in range(2,6):
            rows=self.fixture();rows.pop(index)
            self.assertFalse(any(x['source_continuation_observed'] for x in analyze.classify(rows,'tag')['outcomes']))
        rows=self.fixture();rows[2]['data']=rows[2]['data'].replace('false,false,false','true,false,false')
        self.assertFalse(analyze.classify(rows,'tag')['outcomes'][0]['source_continuation_observed'])

    def test_patch_reversible_and_no_new_post_goto_dynamic_reads(self):
        original=builder.r14.patch_fighter(builder.r14.r07.patch_fighter(builder.r14.r07.sources('scripts/fighter/yihu.json'))[0])[0]
        patched,changes=builder.patch_fighter(original,'tag')
        restored=patched
        for change in changes:
            restored=restored.replace(change['replacement'],change['original'],1)
            after=change['replacement'].split(builder.GOTO,1)[1].split('consumer-goto-after',1)[0]
            self.assertIn('__m002ContinuationSink("continuation-breadcrumb", __m002ContinuationData);',after)
            breadcrumb=after.split('\n')[0]
            for dynamic in ['_root','_parent','this.','escape(']:self.assertNotIn(dynamic,breadcrumb)
        self.assertEqual(restored,original)
        self.assertEqual(patched.count('nornalhit()'),original.count('nornalhit()'))
        self.assertEqual(patched.count('gotoAndPlay('),original.count('gotoAndPlay('))
        with self.assertRaises(ValueError):builder.patch_fighter(patched,'tag')
        with self.assertRaises(ValueError):builder.patch_fighter(original,'bad"tag')


if __name__=='__main__':unittest.main()
