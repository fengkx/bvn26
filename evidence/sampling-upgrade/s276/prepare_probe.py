"""Prepare source-bound UI-only observation patches; never launch or inject input."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUTTON = 'DefineButton2_2009/BUTTONCONDACTION on({}).as'
LISTENER = 'DefineSprite_1991/frame_1/DoAction.as'


def insert_once(source, anchor, addition):
    if source.count(anchor) != 1:
        raise ValueError('ambiguous or missing source anchor')
    patched = source.replace(anchor, anchor + addition)
    if patched.replace(anchor + addition, anchor, 1) != source:
        raise ValueError('source inversion failed')
    return patched


def patches(scripts):
    result = {}
    for event, label in [('keyPress Enter', 'enter_entry'), ('release', 'release_entry')]:
        path = BUTTON.format(event)
        source = scripts[path]
        expected = 'on(keyPress "<Enter>"){\r\n   gotoAndStop(1);\r\n}\r\n' if event == 'keyPress Enter' else 'on(release){\r\n   gotoAndStop(1);\r\n}\r\n'
        if source != expected:
            raise ValueError('changed Button2009 source')
        result[path] = insert_once(source, '{\r\n', f'   _root.s276Observe("{label}", this);\r\n')
    path = LISTENER
    result[path] = insert_once(scripts[path], 'onKeyUp = function()\r\n{\r\n',
                              '   _root.s276Observe("menu_keyup", this);\r\n')
    result[path] = insert_once(result[path], '         case 1:\r\n',
                              '            _root.s276Observe("menu_play_branch", this);\r\n')
    for frame in (1, 10):
        path = f'DefineSprite_2010/frame_{frame}/DoAction.as'
        if scripts[path] != 'stop();\r\n':
            raise ValueError('changed menu stop')
        result[path] = scripts[path] + f'_root.s276Observe("menu_frame{frame}", this);\r\n'
    path = 'frame_1/DoAction.as'
    result[path] = scripts[path] + (HERE / 'observer.as').read_text()
    return result


def prepare(output):
    pins = json.loads((HERE / 'input-sha256.json').read_text())
    for path, expected in pins.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('locked input changed: ' + path)
    scripts = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}
    result = patches(scripts)
    output.mkdir(parents=True, exist_ok=False)
    for path, source in result.items():
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.encode())
    return {path: hashlib.sha256(source.encode()).hexdigest() for path, source in result.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), indent=2))
