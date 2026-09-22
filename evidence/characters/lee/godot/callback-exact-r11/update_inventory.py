#!/usr/bin/env python3
"""Add r11 exact same-run callback rows to the current r10 inventory."""
import json
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parents[5]
here=Path(__file__).resolve().parent
prior=json.loads((root/'evidence/characters/lee/callback-exact-r01/pending-inventory-current-r10.json').read_text())
comparison=json.loads((here/'comparison.json').read_text())
by_frame={}
for case in comparison['cases']:
    if case['status']!='exact_0diff': continue
    for frame in sorted({int(e['source_frame']) for e in case['source_events']}): by_frame[frame]=case
for entry in prior['entries']:
    case=by_frame.get(int(entry['source_frame']))
    if not case or entry['kind']!='frame_action': continue
    prov=case['provenance']
    entry['status']='native_matched'; entry['observed_slots']=[case['slot']]; entry['lee_slots_observed']=[case['slot']]
    entry.pop('remaining_reason',None); entry.pop('provenance_note',None)
    entry['source_raw_captures']=sorted(set(entry.get('source_raw_captures',[])+[prov['source_raw']]))
    entry['godot_exact_scope']={'artifact':'evidence/characters/lee/godot/callback-exact-r11/comparison.json','case_id':case['case_id'],'fields':case['compared_fields'],'differences':[],'source_event_count_for_frame':sum(int(x['source_frame'])==int(entry['source_frame']) for x in case['source_events'])}
    entry['native_provenance']={'fixture':prov['native_fixture'],'fixture_sha256':prov['native_fixture_sha256'],'source_raw':prov['source_raw'],'source_raw_sha256':prov['source_raw_sha256'],'source_build':prov['source_build_copy'],'source_build_sha256':prov['source_build_sha256'],'native_log':'evidence/characters/lee/godot/callback-exact-r11/engine.log','native_log_sha256':comparison['godot_log_sha256'],'runtime_hash':'ddfce1b11f6b211dad81dda22105e5d17ae97d2a9e329d40270cfda719a66510'}
    entry['matched_fields']=case['compared_fields']; entry['differences']=[]
prior['schema']='lee-callback-inventory-current-r11'
prior['scope']='Current-derived 49-row inventory with r05-r11 same-source-run bounded callback comparisons. Matches cover source_frame, entering, action and decoded ql only; not full-state parity.'
counts=Counter(e['status'] for e in prior['entries'])
prior['counts']={k:counts[k] for k in ('native_matched','source_only','remaining','normal_input_unreachable')}
out=root/'evidence/characters/lee/callback-exact-r01/pending-inventory-current-r11.json'
out.write_text(json.dumps(prior,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(prior['counts'],ensure_ascii=False))
