"""Compile the shared snapshot/fade service, rejecting unaudited function bodies."""
import hashlib
import json
from pathlib import Path
import re

try:
    from .compile_hit_receive import extract_function
except ImportError:
    from compile_hit_receive import extract_function

ROOT = Path(__file__).resolve().parents[2]
# These whole-function fingerprints cover control flow and statement order,
# not just the constants extracted below. Changed behavior needs a new audit.
AUDITED = {
    'showdow': '9e0cc3c457f93f97117097b10808ae4502563b0a966552d3e8c871e232268186',
    'shadowEffect': 'c82a3a779558348239baf7fd7cdbf76e99ebf8b30a68eb20796231bc30c1ba38',
}


def checked_function(source: str, name: str) -> str:
    function = extract_function(source, name)
    digest = hashlib.sha256(''.join(function.split()).encode()).hexdigest()
    if digest != AUDITED[name]:
        raise ValueError(f'Unaudited {name} body: {digest}')
    return function


def build() -> dict:
    sources = []
    for path in [ROOT / 'scripts/main.json', *sorted((ROOT / 'scripts/fighter').glob('*.json'))]:
        bundle = json.loads(path.read_text())
        name = 'shadowEffect' if path.name == 'main.json' else 'showdow'
        script = next(s for s in bundle['scripts'] if f'function {name}(' in s['source'])
        function = checked_function(script['source'], name)
        if name == 'showdow' and 'var _si = 0;' not in script['source']:
            raise ValueError('Missing wrapper-lifetime counter initialization')
        sources.append({'bundle': str(path.relative_to(ROOT)), 'path': script['path'],
                        'swf_sha256': bundle['swf_sha256'], 'function': function,
                        'sha256': hashlib.sha256(function.encode()).hexdigest()})
    controller_sources = []
    for fighter in ('minren', 'yihu', 'rifagu'):
        bundle = json.loads((ROOT / f'scripts/fighter/{fighter}.json').read_text())
        for script in bundle['scripts']:
            if 'function initCtrl()' not in script['source']:
                continue
            function = extract_function(script['source'], 'initCtrl')
            compact = ''.join(function.split())
            expected = 'if(_parent.useAI){AImain.gotoAndStop(2);_root.airanset=setInterval(randAI,500);}else{AImain.gotoAndStop(1);AImain.unloadMovie();}'
            if expected not in compact:
                raise ValueError('Unaudited controller display lifetime')
            controller_sources.append({'fighter': fighter, 'path': script['path'], 'function': function})
    main = sources[0]['function']
    wrapper = sources[1]['function']
    layer = re.search(r'var _loc7_ = _root.game.(\w+);', main)[1]
    depths = set()
    for path in sorted((ROOT / 'godot/generated/stages/catalog').glob('frame_*/timeline.json')):
        timeline = json.loads(path.read_text())
        for frame in timeline['frames']:
            for placement in frame['display_list']:
                if placement.get('name') == layer:
                    depths.add(placement['depth'])
    if len(depths) != 1:
        raise ValueError(f'Shadow layer depth differs across stages: {depths}')
    return {'format': 'bvn26-shadow-v1', 'sources': sources,
            'controller_sources': controller_sources,
            'controller': {'instance': 'AImain', 'cpu_frame': 2, 'player_unloaded': True},
            'counter_initial': 0, 'counter_skip_above': int(re.search(r'\+\+_si > (\d+)', wrapper)[1]),
            'alpha_start': int(re.search(r'alphaStart:(\d+)', wrapper)[1]),
            'alpha_lose': int(re.search(r'alphaLose:(\d+)', wrapper)[1]),
            'layer': layer, 'layer_depth': depths.pop(),
            'snapshot': 'bitmap_draw_local_bounds', 'fade_during_gameplay_pause': True,
            'counter_lifetime': 'fighter_wrapper'}


if __name__ == '__main__':
    output = ROOT / 'godot/generated/main/shadow.json'
    output.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + '\n')
