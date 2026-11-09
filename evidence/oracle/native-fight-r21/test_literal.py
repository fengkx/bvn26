import gzip
import json
import re
import unittest
import analyze
import build_observer as builder


class LiteralTests(unittest.TestCase):
    def fixture(self):
        old=builder.HERE.parent/'native-fight-r20'
        tag=json.loads((old/'build.json').read_text())['run_id']
        raw=(old/'run-01/combined.log').read_bytes()
        line=next(x for x in raw.splitlines() if x.startswith(b'M002SIDE|'))
        literal=b'M002LITERAL|'+tag.encode()+b'|doAllAction|'
        raw=raw.replace(line+b'\n',line+b'\n'+literal+b'before\n'+literal+b'after\n',1)
        records,rows=analyze.parse(raw,tag)
        return records,rows,tag

    def test_synthetic_match_never_admits(self):
        records,rows,tag=self.fixture();r=analyze.classify(records,rows,tag)
        self.assertEqual(r['outcomes'][0]['classification'],'matched-literal-source')
        for flag in analyze.r19.r17.FLAGS:self.assertIs(r[flag],False)

    def test_missing_interleaved_duplicate_and_wrong_site(self):
        for mode in ['missing','interleave','duplicate','site','bridge']:
            records,rows,tag=self.fixture();i=next(i for i,r in enumerate(records) if r['kind']=='literal' and r['phase']=='after')
            if mode=='missing':records.pop(i)
            elif mode=='interleave':records.insert(i,dict(kind='unclassified',data='barrier'))
            elif mode=='duplicate':records.insert(i,dict(records[i]))
            elif mode=='site':records[i]['site']='doStand'
            else:records.pop(i-2)
            with self.subTest(mode=mode):self.assertFalse(any(x['source_continuation_observed'] for x in analyze.classify(records,rows,tag)['outcomes']))

    def test_orphan_after_refused(self):
        records,rows,tag=self.fixture();after=next(r for r in records if r['kind']=='literal' and r['phase']=='after')
        self.assertEqual(analyze.classify([after],rows,tag)['outcomes'][0]['classification'],'literal-after-without-before')

    def test_foreign_literal_tag_refused(self):
        old=builder.HERE.parent/'native-fight-r20';tag=json.loads((old/'build.json').read_text())['run_id']
        raw=(old/'run-01/combined.log').read_bytes()+b'M002LITERAL|foreign|doAllAction|after\n'
        with self.assertRaisesRegex(ValueError,'Foreign/malformed literal'):analyze.parse(raw,tag)

    def test_patch_restores_source_and_original_calls(self):
        original=gzip.decompress((builder.HERE/'r20-reconstructed-source.as.gz').read_bytes()).decode()
        patched,changes=builder.patch_fighter(original,'tag');restored=patched
        for c in changes:restored=restored.replace(c['replacement'],c['original'],1)
        self.assertEqual(restored,original)
        for token in ['gotoAndPlay(', 'nornalhit()']:self.assertEqual(patched.count(token),original.count(token))
        with self.assertRaises(ValueError):builder.patch_fighter(patched,'tag')
        with self.assertRaises(ValueError):builder.patch_fighter(original,'bad"tag')

    def test_pcode_after_uses_literal_not_register(self):
        old=gzip.decompress((builder.HERE/'r20-sprite16.pcode.gz').read_bytes()).decode().replace('\r','')
        new=gzip.decompress((builder.HERE/'r21-sprite16.pcode.gz').read_bytes()).decode().replace('\r','')
        goto=r'Push "砍1"\nPush 1\nPush register\d+\nPush "gotoAndPlay"\nCallMethod\nPop\n'
        self.assertEqual(len(re.findall(goto+r'Push register\d+\nTrace',old)),2)
        for site in ['doStand','doAllAction']:
            before='Push "M002LITERAL|m002-r21-offline-20261110|'+site+'|before"\nTrace\n'
            after='Push "M002LITERAL|m002-r21-offline-20261110|'+site+'|after"\nTrace\n'
            self.assertEqual(len(re.findall(re.escape(before)+goto+re.escape(after),new)),1)

    def test_historical_comparison_preserves_refusals(self):
        r=analyze.replay()
        for run in r['runs'].values():
            self.assertEqual(run['literal']['outcomes'],[])
            self.assertEqual(run['structural_refusal'],'Incomplete actor state at clock boundary')
            self.assertEqual(run['sink']['outcomes'][0]['cause'],'unproved')
        self.assertEqual(r['runs']['r18']['direct']['outcomes'],[])
        self.assertEqual(r['runs']['r20']['direct']['outcomes'][0]['classification'],'before-without-after')


if __name__=='__main__':unittest.main()
