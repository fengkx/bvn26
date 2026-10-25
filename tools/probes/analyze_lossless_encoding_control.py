"""Validate the isolated encoding intervention and compare both native paths without rewriting references."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_component_fill_api import ROOT,analyze as compare_api


def analyze(native,output=None):
    build=json.loads((native/'build.json').read_text());proof=build['encoding_variant'];fixture=json.loads((ROOT/build['fixture_source']).read_text());raw=fixture['leaves']['8']['pixels_premultiplied']
    assert proof['bitmap_id']==7 and proof['before_format']==3 and proof['after_format']==5
    assert proof['before_bitmap_tag_sha256']==fixture['raw_tag_sha256']['7']
    assert proof['decoded_rgba_sha256']==hashlib.sha256(bytes(c for p in raw for c in p)).hexdigest()
    assert proof['all_other_tags_byte_identical'] and proof['unchanged_tag_count']==646
    assert proof['after_swf_sha256']==build['outputs_sha256']['game/main.swf']
    result=compare_api(native,output)
    return {'encoding_intervention':proof,'comparisons':result,'format5_variant_matches_as':result['api_equivalence_verified'],'original_indexed_sampling_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n');print('format5 variant exact against AS',r['format5_variant_matches_as'])
