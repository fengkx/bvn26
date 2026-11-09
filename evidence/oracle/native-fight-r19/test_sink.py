import copy
import gzip
import re
import unittest
import analyze
import build_observer as builder


class SinkTests(unittest.TestCase):
    def fixture(self):
        q='/game/p1/mc/helper,1,doAllAction,/game/p1/mc,frame,false'
        events=[('decision-installed','yihu-sprite16,/game/p1/mc/helper'),('consumer-query-before',q)]
        events += [('fight-key-return',f'yihu-decision-{i},74,{v},/game/p1/mc,false,false,false,4,x,y') for i,v in zip(range(9,13),['true','false','false','false'])]
        events += [('consumer-predicate-result','/game/p1/mc/helper,1,doAllAction,true'),('consumer-goto-before',q),('continuation-prep','tag,/game/p1/mc/helper,1,doAllAction')]
        rows=[dict(seq=i,kind=k,data=d) for i,(k,d) in enumerate(events,1)]
        records=copy.deepcopy(rows)+[dict(kind='direct',phase=phase,data=rows[-1]['data']) for phase in ['before','after']]
        return records,rows

    def test_match_never_admits(self):
        records,rows=self.fixture();r=analyze.classify(records,rows,'tag')
        self.assertEqual(r['outcomes'][0]['classification'],'matched-direct-trace')
        for flag in analyze.r17.FLAGS:self.assertIs(r[flag],False)

    def test_missing_and_orphan(self):
        records,rows=self.fixture()
        self.assertEqual(analyze.classify(records[:-1],rows,'tag')['outcomes'][0]['classification'],'before-without-after')
        self.assertEqual(analyze.classify(records[-1:],rows,'tag')['outcomes'][0]['classification'],'after-without-before')

    def test_interleave_duplicate_foreign_identity_missing_prefix(self):
        for mode in ['interleave','duplicate','identity','prefix','prep']:
            records,rows=self.fixture()
            if mode=='interleave':records.insert(-1,dict(kind='unclassified',data='unknown log'))
            elif mode=='duplicate':records.append(copy.deepcopy(records[-1]))
            elif mode=='identity':records[-1]['data']='foreign'
            elif mode=='prefix':rows.pop(3)
            else:records.pop(-3)
            with self.subTest(mode=mode):self.assertFalse(any(x['source_continuation_observed'] for x in analyze.classify(records,rows,'tag')['outcomes']))

    def test_combined_parser_preserves_unknown_ordering_barrier(self):
        old=builder.HERE.parent/'native-fight-r18'
        import json
        tag=json.loads((old/'build.json').read_text())['run_id']
        lines=(old/'run-01/tagged.log').read_bytes().splitlines()
        identity=lines[8216].split(b'|',7)[7]
        side=[b'M002SIDE|'+identity+b'|before',b'M002SIDE|'+identity+b'|after']
        raw=b'\n'.join(lines[:8217]+side+lines[8217:])+b'\n'
        records,rows=analyze.parse_combined(raw,tag)
        self.assertEqual(analyze.classify(records,rows,tag)['outcomes'][0]['classification'],'matched-direct-trace')
        raw=b'\n'.join(lines[:8217]+side[:1]+[b'unclassified trace']+side[1:]+lines[8217:])+b'\n'
        records,rows=analyze.parse_combined(raw,tag)
        self.assertFalse(analyze.classify(records,rows,tag)['outcomes'][0]['source_continuation_observed'])

    def test_foreign_raw_side_tag_rejected(self):
        with self.assertRaisesRegex(ValueError,'Foreign/malformed side'):analyze.parse_combined(b'M002SIDE|foreign,h,1,doAllAction|after\n','tag')

    def test_bytecode_has_direct_trace_not_root_call(self):
        p=builder.HERE
        old=gzip.decompress((p/'r18-sprite16.pcode.gz').read_bytes()).decode().replace('\r','')
        new=gzip.decompress((p/'r19-sprite16.pcode.gz').read_bytes()).decode().replace('\r','')
        # Only the exact original attack goto sites, not unrelated native gotos.
        old_pattern=r'Push "砍1"\nPush 1\nPush register\d+\nPush "gotoAndPlay"\nCallMethod\nPop\nPush register\d+\nPush "continuation-breadcrumb"'
        new_pattern=r'Push register\d+\nTrace\nPush "砍1"\nPush 1\nPush register\d+\nPush "gotoAndPlay"\nCallMethod\nPop\nPush register\d+\nTrace\nPush register\d+\nPush "continuation-breadcrumb"'
        self.assertEqual(len(re.findall(old_pattern,old)),2)
        self.assertEqual(len(re.findall(new_pattern,new)),2)

    def test_exact_patch_reversal(self):
        source=gzip.decompress((builder.HERE/'r18-reconstructed-source.as.gz').read_bytes()).decode()
        patched,old,new=builder.patch_fighter(source)
        self.assertEqual(patched.replace(new,old),source)
        self.assertEqual(patched.count('gotoAndPlay('),source.count('gotoAndPlay('))
        self.assertEqual(patched.count('nornalhit()'),source.count('nornalhit()'))
        with self.assertRaises(ValueError):builder.patch_fighter(patched)

    def test_historical_cause_stays_unproved(self):
        r=analyze.replay();self.assertEqual(r['outcomes'],[])
        self.assertEqual(r['r17_pairing']['outcomes'][0]['classification'],'prep-without-breadcrumb')
        self.assertEqual(r['r17_pairing']['outcomes'][0]['cause'],'unproved')
        self.assertEqual(r['structural_refusal'],'Incomplete actor state at clock boundary')


if __name__=='__main__':unittest.main()
