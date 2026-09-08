"""Compile the source HP HUD placements and rasterized shape layers."""
import argparse
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from extract_timeline_geometry import extract_frames, placement_delta, file_sha256


def build(workspace, shapes, output):
    xml = workspace / 'main.xml'
    root = ET.parse(xml).getroot()
    timeline = extract_frames(xml, 1814)
    definitions = {d['character_id']: d for d in timeline['definitions']}
    wrapper = extract_frames(xml, 1815)['frames'][4]['display_list']
    placement = next(p for p in wrapper if p['character_id'] == 1814)
    outer = next(placement_delta(t) for t in root.findall('./tags/item') if t.get('name') == 'xuetiao')
    output.mkdir(parents=True, exist_ok=True)
    layers = {}
    for frame in range(1, 21):
        shutil.copyfile(shapes / 'DefineSprite_1788' / f'{frame}.png', output / f'low-{frame}.png')
    for sid in [591, 1787, 1792, 1796, 1812]:
        shutil.copyfile(shapes / f'{sid}.png', output / f'{sid}.png')
        layers[str(sid)] = definitions[sid]['shape_bounds_twips']
    mask = next(t for t in root.iter('item') if t.get('shapeId') == '1797')
    points = []
    x = y = 0
    for record in mask.findall('./shapes/shapeRecords/item'):
        kind = record.get('type')
        if kind == 'StyleChangeRecord' and record.get('stateMoveTo') == 'true':
            x, y = int(record.get('moveDeltaX')), int(record.get('moveDeltaY'))
            points.append([x / 20, y / 20])
        elif kind == 'StraightEdgeRecord':
            x += int(record.get('deltaX', 0)); y += int(record.get('deltaY', 0))
            points.append([x / 20, y / 20])
        elif kind == 'CurvedEdgeRecord':
            cx, cy = x + int(record.get('controlDeltaX')), y + int(record.get('controlDeltaY'))
            ex, ey = cx + int(record.get('anchorDeltaX')), cy + int(record.get('anchorDeltaY'))
            for step in range(1, 17):
                t = step / 16
                points.append([((1-t)**2*x+2*(1-t)*t*cx+t*t*ex)/20, ((1-t)**2*y+2*(1-t)*t*cy+t*t*ey)/20])
            x, y = ex, ey
    spec = {'source_sha256': file_sha256(Path('game/main.swf')), 'outer': outer,
            'placement': placement, 'parts': timeline['frames'][0]['display_list'],
            'bar_parts': definitions[1794]['first_frame_display_list'],
            'head_parts': definitions[1798]['first_frame_display_list'],
            'layers': layers, 'mask': points}
    (output / 'presentation.json').write_text(json.dumps(spec, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--ffdec-jar', type=Path, required=True)
    p.add_argument('--raster-workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(a.ffdec_jar), '-selectid',
                    '591,1787,1788,1792,1796,1812', '-format', 'shape:png', '-export',
                    'shape', str(a.raster_workspace), 'game/main.swf'], check=True)
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(a.ffdec_jar), '-selectid',
                    '1788', '-export', 'sprite', str(a.raster_workspace), 'game/main.swf'], check=True)
    build(a.workspace, a.raster_workspace, a.output)
