"""Extract the shared training recovery callback and its wall-clock interval."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def build():
    bundle = json.loads((ROOT / 'scripts/main.json').read_text())
    path = 'DefineSprite_1991/frame_1/DoAction.as'
    source = next(s['source'] for s in bundle['scripts'] if s['path'] == path)
    function = source[source.index('function zdbx()'):source.index('function getCenter(')].strip()
    compact = re.sub(r'\s+', '', function)
    expected = 'functionzdbx(){if(_root.p2loaded==true){'
    for slot in ['p1', 'p2']:
        expected += f'if(_root.game.{slot}.mc.beida==0){{_root.game.{slot}.mc.hp=_root.maxhp;_root.game.{slot}.mc.ql=300;}}'
    expected += '}}'
    if compact != expected:
        raise ValueError('Uncompiled training recovery body')
    interval = re.search(r'if\(_root.modo == (\d+)\)\s*\{\s*_root.zdbxint = setInterval\(zdbx,(\d+)\);', source)
    if not interval:
        raise ValueError('Missing training recovery timer registration')
    result = {'format': 'bvn26-training-recovery-v1', 'mode': int(interval[1]),
              'interval_ms': int(interval[2]), 'energy': 300, 'receiver_state': 0,
              'source_path': path, 'source_text': function,
              'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'source_swf': {'path': bundle['game_file'], 'sha256': bundle['swf_sha256']}}
    output = ROOT / 'godot/generated/main/training.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    build()
