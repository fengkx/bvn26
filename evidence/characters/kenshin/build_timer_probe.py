"""Add callback boundary observations to the existing character-SOP probe.

Authored setInterval calls, callback bodies, and their delivery stay unchanged.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/probes'))
import build_ai_reference as probe

original_instrument = probe.instrument
original_helper_observer = probe.helper_observer_source


def helper_observer(names):
    source = original_helper_observer(names)
    needle = '_root.aiHelperState = function(player)\n{'
    assert source.count(needle) == 1
    return source.replace(needle, needle + '''
   var wrapper = _root.game[player];
   var sibling = wrapper.getInstanceAtDepth(45 - 16384);
   _root.aiEvent("wrapper_state", player + "," + wrapper._currentframe + "," + wrapper.mc._currentframe + "," + sibling._currentframe);
''')


def instrument(source, origin, fighter):
    source = original_instrument(source, origin, fighter)
    if not origin.startswith('fighter/Kenshin#'):
        return source
    def observe(match):
        marker = json.dumps(origin, ensure_ascii=False)
        payload = marker + ' + "," + String(_this) + "," + _root.aiNumber(_this.hp)'
        return (match[1] + '\n   _root.aiEvent("form_interval_enter", ' + payload + ');\n'
                + match[2] + '\n   _root.aiEvent("form_interval_exit", ' + payload + ');\n' + match[3])
    return re.sub(r'(feixue = function\(\)\s*\{)(.*?)(^\};)', observe, source, flags=re.M | re.S)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', type=Path, required=True)
    args = parser.parse_args()
    probe.instrument = instrument
    probe.helper_observer_source = helper_observer
    result = probe.build(args.ffdec.resolve(), args.output.resolve(), 'kenshin-timer-r01', int(json.loads(args.case.read_text())['frames']),
                         move_case=args.case.resolve(), dynamic_move_case=True,
                         p1_character='剑心', p2_character='一护', p1_helper='我爱罗', p2_helper='魂',
                         profile='diagnostic', diagnostic_auto_start=True,
                         diagnostic_key_injection=True, diagnostic_trace_hooks=True)
    print(json.dumps({'status': result['status'], 'output': str(args.output)}))
