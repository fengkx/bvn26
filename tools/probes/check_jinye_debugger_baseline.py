"""Check instrumented workload output as sanity evidence, never as a pixel reference."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from tools.probes.analyze_jinye_profile import append_row
from tools.probes.analyze_jinye_materialization import decode
from tools.probes.build_bound_bitmap_component import ROOT,source_tags


def check(native):
    fixture=json.loads((native/'fixture.json').read_text());build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest()==build['fixture_sha256']
    assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    old,images,readbacks=decode(ROOT/'evidence/importer-loud-fail/r242/native')
    assert fixture=={**old,'profile_workload':'direct_uncached','minimum_duration_ms':fixture['minimum_duration_ms'],'draws_per_batch':1000}
    assert fixture['minimum_duration_ms'] in (20000,60000)
    assert hashlib.sha256((native/'game/main.swf').read_bytes()).hexdigest()==build['swf_sha256']
    raw={str(struct.unpack_from('<H',p)[0]):hashlib.sha256(r).hexdigest() for c,p,r in source_tags(native/'game/main.swf') if c in (2,35)}
    assert raw==fixture['raw_tag_sha256']
    events=[line.split('|') for line in (native/'native.log').read_text().splitlines() if line.startswith('AIREF|')]
    expected=['image']+['row']*40+['matrix','profile','iterations','props','image']+['row']*400+['done'];assert len(events)==len(expected)
    actual={};active=None
    for index,(event,kind) in enumerate(zip(events,expected)):
        assert len(event)==8 and event[1]==build['run_id'] and event[2:6]==[str(index),'0','0','0'] and event[6]==kind
        values=event[7].split(',')
        if kind=='image':
            label='source' if not actual else 'final';size=[92,40] if label=='source' else [600,400]
            assert values==[label,*map(str,size),'true'];active={'size':size,'pixels':[],'raw':[]};actual[label]=active
        elif kind=='row':append_row(active,values)
        elif kind=='matrix':assert list(map(float,values))==readbacks['matrix'][0]
        elif kind=='profile':assert event[7]=='direct_uncached;actual-source;caller-sampling-only'
        elif kind=='iterations':assert int(values[0])>0 and int(values[0])%1000==0 and int(values[1])>=fixture['minimum_duration_ms']
        elif kind=='props':assert values==['direct_uncached','false','0','1']
        else:assert event[7]=='ok'
    assert actual['source']==images['source'] and actual['final']==images['0-direct']
    return {'source_pixels_exact':3680,'final_raw_rgba_exact':240000,'final_premultiplied_rgba_exact':240000,'raw_tags_after_final_import':raw,'instrumented_pixel_reference':False,'production_admitted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.write_text(json.dumps(check(args.native),indent=2)+'\n')
