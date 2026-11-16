"""Observe retained undefined-call sites without replacing their source calls."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/probes'))
import build_ai_reference as probe

original = probe.instrument


def instrument(source, origin, fighter):
    source = original(source, origin, fighter)
    if origin.startswith('fighter/ichigo#'):
        def interval(match):
            payload = json.dumps(origin) + ' + "," + String(_this) + "," + _root.aiNumber(_this.hp)'
            return (match[1] + '\n   _root.aiEvent("form_interval_enter", ' + payload + ');\n'
                    + match[2] + '\n   _root.aiEvent("form_interval_exit", ' + payload + ');\n' + match[3])
        source = re.sub(r'(feixue = function\(\)\s*\{)(.*?)(^\};)',
                        interval, source, flags=re.M | re.S)
    if origin != 'fighter/ichigo#DefineSprite_632/frame_300/PlaceObject2_386_36/CLIPACTIONRECORD onClipEvent(enterFrame).as':
        return source
    for direction in (1, -1):
        call = f'_parent.setDirect({direction});'
        assert source.count(call) == 1
        def event(phase):
            return ('_root.aiEvent("ichigo_direct_' + phase + '", "' + str(direction)
                    + '," + typeof(_parent.setDirect) + "," + _parent._parent._xscale'
                    + ' + "," + _parent._currentframe);')
        source = source.replace(call, event('before') + '\n' + call + '\n' + event('after'))
    return source


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('ffdec', 'output', 'case'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    probe.instrument = instrument
    result = probe.build(args.ffdec.resolve(), args.output.resolve(), 'ichigo-direct-r01', 360,
                         move_case=args.case.resolve(), dynamic_move_case=True,
                         p1_character='一护2', p2_character='一护', p1_helper='我爱罗', p2_helper='魂',
                         profile='diagnostic', diagnostic_auto_start=True,
                         diagnostic_key_injection=True, diagnostic_trace_hooks=True)
    print(json.dumps({'status': result['status'], 'output': str(args.output)}))
