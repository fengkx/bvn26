"""Native MovieClip hierarchy plus authored display records; no pixel parity claim."""
import argparse
import copy
import json
import math
from pathlib import Path
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET

from tools.probes.collect_ai_reference import decode_number
from tools.sampling_native import validate, sha


def xml_record(element):
    return {'tag': element.tag, 'attributes': dict(element.attrib),
            'children': [xml_record(child) for child in element]}


def source_timelines(xml):
    root = ET.parse(xml).getroot()
    symbols = {}
    timelines = {0: root.find('tags')}
    for tag in root.find('tags'):
        identity = next((tag.get(k) for k in ('spriteId', 'shapeId', 'characterId', 'textId', 'buttonId') if tag.get(k)), None)
        if identity:
            symbols[int(identity)] = tag.get('type')
        if tag.get('type') == 'DefineSpriteTag':
            timelines[int(tag.get('spriteId'))] = tag.find('subTags')
    frames = {}
    for symbol, tags in timelines.items():
        display, snapshots = {}, []
        for index, tag in enumerate(tags):
            kind = tag.get('type', '')
            if kind.startswith('PlaceObject'):
                depth = int(tag.get('depth'))
                moving = tag.get('placeFlagMove') == 'true'
                if moving and depth not in display:
                    raise ValueError('source MOVE at absent depth')
                record = copy.deepcopy(display[depth]) if moving else {'attributes': {}, 'fields': {}}
                record['attributes'].update(tag.attrib)
                for child in tag:
                    record['fields'][child.tag] = xml_record(child)
                record['last_tag_index'] = index
                if not moving or tag.get('characterId'):
                    record['placement_frame'] = len(snapshots)+1
                display[depth] = record
            elif kind in ('RemoveObjectTag', 'RemoveObject2Tag'):
                display.pop(int(tag.get('depth')), None)
            elif kind == 'ShowFrameTag':
                snapshots.append(copy.deepcopy(display))
        frames[symbol] = snapshots
    return frames, symbols


def collect(lines, run_id, frames):
    samples, current = [], None
    for line in lines:
        p = line.split('|', 7)
        if len(p) != 8 or p[:2] != ['AIREF', run_id]:
            raise ValueError('foreign/malformed display event')
        tick, kind, value = int(p[5]), p[6], p[7]
        if not kind.startswith('display_'):
            continue
        if kind == 'display_begin':
            if current is not None or tick != len(samples):
                raise ValueError('missing/duplicate display sample')
            current = {'tick': tick, 'nodes': {}}
            continue
        if current is None or tick != current['tick']:
            raise ValueError('display event outside sample')
        f = value.split(',')
        if kind == 'display_camera':
            if 'camera' in current or len(f) != 16:
                raise ValueError('missing/duplicate camera fields')
            nums = [decode_number(x) for x in f[4:]]
            if not all(math.isfinite(x) for x in nums):
                raise ValueError('nonfinite camera')
            current['camera'] = {'stage_width': int(f[0]), 'stage_height': int(f[1]),
                                 'scale_mode': f[2], 'align': f[3],
                                 'root_matrix': nums[:6], 'root_global_matrix': nums[6:]}
        elif kind == 'display_node':
            if len(f) != 24:
                raise ValueError('incomplete display node')
            path, parent, identity, source = map(unquote, f[:4])
            if path in current['nodes']:
                raise ValueError('duplicate display node')
            nums = [decode_number(x) for x in f[6:18]]
            if not all(math.isfinite(x) for x in nums):
                raise ValueError('nonfinite display matrix')
            current['nodes'][path] = {'parent': parent, 'instance_id': identity, 'source_script': source,
                'depth': int(f[4]), 'frame': int(f[5]), 'matrix': nums[:6], 'global_matrix': nums[6:],
                'visible': f[18], 'alpha': decode_number(f[19]), 'blend_mode': f[20],
                'cache_as_bitmap': f[21], 'scroll_rect': f[22], 'filter_count': int(f[23]), 'filters': []}
        elif kind == 'display_filter':
            node = current['nodes'][unquote(f[0])]
            if int(f[1]) != len(node['filters']):
                raise ValueError('missing/out-of-order filter')
            node['filters'].append({k: unquote(v) for k,v in
                                    (pair.split('=',1) for pair in f[2].split(';') if pair)})
        elif kind == 'display_children':
            node = current['nodes'][unquote(f[0])]
            if 'child_count' in node:
                raise ValueError('duplicate child inventory')
            node['child_count'] = int(f[1])
        elif kind == 'display_end':
            nodes = current['nodes']
            if int(value) != len(nodes) or 'camera' not in current or '_level0.game' not in nodes:
                raise ValueError('missing nodes or camera')
            for path, node in nodes.items():
                if path != '_level0.game' and node['parent'] not in nodes:
                    raise ValueError('dropped parent hierarchy')
                if node.get('child_count') != sum(n['parent']==path for n in nodes.values()):
                    raise ValueError('dropped child hierarchy')
                if not math.isfinite(node['alpha']):
                    raise ValueError('nonfinite display alpha')
                if node['filter_count'] != len(node['filters']):
                    raise ValueError('dropped filter')
            samples.append(current)
            current = None
        else:
            raise ValueError('unsupported display event')
    if current is not None or len(samples) != frames+1:
        raise ValueError('missing display samples')
    return samples


def enrich(samples, exports):
    databases = {source: source_timelines(path) for source,path in exports.items()}
    gaps = []
    previous = {}
    for sample in samples:
        nodes = sample['nodes']
        for path, node in nodes.items():
            match = re.fullmatch(r'(game/[^#]+)#(?:DefineSprite_(\d+)/)?frame_\d+/DoAction.as',node['source_script'])
            if match:
                node['source_swf'], node['symbol'] = match[1], int(match[2] or 0)
            else:
                parent = nodes.get(node['parent'], {})
                if 'authored_children' in parent:
                    placement = parent['authored_children'].get(str(node['depth']+16384))
                    if placement and 'characterId' in placement['attributes']:
                        node['source_swf'], node['symbol'] = parent['source_swf'], int(placement['attributes']['characterId'])
            if 'symbol' not in node:
                gaps.append({'tick':sample['tick'],'path':path,'reason':'unresolved runtime symbol'})
                continue
            timeline, symbols = databases[node['source_swf']]
            symbol = node['symbol']
            if symbol not in timeline or not 1<=node['frame']<=len(timeline[symbol]):
                gaps.append({'tick':sample['tick'],'path':path,'reason':'missing source frame'})
                continue
            authored = timeline[symbol][node['frame']-1]
            node['authored_children'] = {str(depth):record for depth,record in authored.items()}
            observed_depths = {n['depth']+16384 for n in nodes.values() if n['parent']==path}
            for depth,record in authored.items():
                child_symbol = int(record['attributes'].get('characterId',-1))
                if symbols.get(child_symbol)=='DefineSpriteTag' and depth not in observed_depths:
                    gaps.append({'tick':sample['tick'],'path':path,'depth':depth,'reason':'authored MovieClip absent from observed hierarchy'})
        now = {p:n['instance_id'] for p,n in nodes.items()}
        sample['created_since_previous_sample'] = [p for p in now if previous.get(p)!=now[p]]
        sample['removed_since_previous_sample'] = [p for p in previous if now.get(p)!=previous[p]]
        previous = now
    return gaps


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--exports',type=Path,required=True,help='JSON mapping locked source SWFs to XML export paths and hashes')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        receipt_hash=validate(args.case,args.receipt)
        receipt=json.loads(args.receipt.read_text()); build=json.loads((Path(receipt['build'])/'build.json').read_text())
        if not build.get('sampling_display'): raise ValueError('missing display probe')
        exports=json.loads(args.exports.read_text())
        paths={}
        for source,entry in exports.items():
            path=Path(entry['xml'])
            if build['sources_sha256'][source]!=entry['source_sha256'] or sha(path)!=entry['xml_sha256']:
                raise ValueError('source export hash mismatch')
            paths[source]=path
        samples=collect(Path(receipt['trace']).read_text().splitlines(),build['run_id'],build['move_case']['frames'])
        gaps=enrich(samples,paths)
        result={'case_id':build['move_case']['id'],'receipt_sha256':receipt_hash,'samples':samples,'source_gaps':gaps,
                'native_parity_proven':False,'production_admitted':False,'sample_coverage_complete': True, 'source_binding_complete': not gaps,
                'complete': False, 'dynamic_mask_capture_complete': False,
                'camera_scope':'logical stage viewport, root and complete sampled game transform chain; not framebuffer pixels'}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        if gaps: raise ValueError(f'{len(gaps)} unresolved source/hierarchy obligations; see output')
        raise ValueError('dynamic mask ownership not captured; full display/camera evidence incomplete')
    except (ValueError,OSError,KeyError,TypeError) as e:parser.exit(1,f'display evidence error: {e}\n')


if __name__=='__main__':main()
