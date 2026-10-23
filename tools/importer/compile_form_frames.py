"""Compile complete transformation frame blocks for the replacement consumer.

Admission is opt-in until a complete profile graph is validated. Partial matches
must never strip a statement from a transformation preparation block.
"""
import hashlib
import re

from parent_form_requirements import parent_form_requirement


def compile_form_frame(bundle: dict, text: str, path: str, frame: int, parent_frame: int):
    # Whitespace inside a selection string is data, not formatting.
    compact = re.sub(r'"(?:\\.|[^"\\])*"|\s+',
                     lambda match: match[0] if match[0].startswith('"') else '', text)
    location = f"{bundle['game_file']}:{path}"
    common = {'path': path, 'frame': frame, 'line': 1,
              'source_sha256': hashlib.sha256(text.encode()).hexdigest()}
    if compact == 'wankai();':
        requirement = parent_form_requirement(bundle, parent_frame + 1, location)
        return [{**common, 'op': 'body_form_call', 'method': 'wankai', 'replacement': requirement}]
    jump = re.fullmatch(r'_parent.gotoAnd(Play|Stop)\((\d+)\);', compact)
    if jump:
        if jump[1] == 'Play':
            raise ValueError(f'{location}: parent gotoAndPlay requires an unimplemented parent timeline clock')
        requirement = parent_form_requirement(bundle, int(jump[2]), location)
        return [{**common, 'op': 'parent_form_goto', 'target_frame': int(jump[2]),
                 'play': jump[1] == 'Play', 'replacement': requirement}]
    prepare = re.fullmatch(
        r'if\(pn==(1|2)\)\{zn=(1|2);_root\.p([12])bs="([^"\\]+)";'
        r'_parent\.中转\.ql=ql;_parent\.中转\.hp=hp;feixue=function\(\)\{'
        r'if\(_root\.zhanting==false\)\{if\(_root\.game\.p([12])\.mc\.hp>_root\.maxhp/5\)'
        r'\{_root\.game\.p([12])\.mc\.hp-=10;\}\}\};\}', compact)
    if prepare:
        pn, zn, slot, selection, read_slot, write_slot = prepare.groups()
        if int(pn) + int(slot) != 3 or zn != slot or read_slot != slot or write_slot != slot:
            raise ValueError(f'{location}: unsupported form callback receiver/selector relationship')
        return [{**common, 'op': 'form_prepare_slot', 'pn': int(pn), 'zn': int(zn),
                 'slot': 'p' + slot, 'selection': selection, 'callback': 'slot_health'}]
    if compact == ('if(zn==1){_root.feiint=setInterval(feixue,1000);}'
                   'else{_root.feiint2=setInterval(feixue,1000);}_parent.万解=true;'):
        return [{**common, 'op': 'form_start_interval', 'selector_field': 'zn', 'delay_ms': 1000}]
    if re.search(r'\bwankai\s*\(|_parent\.中转\b|\bsetInterval\s*\(|_parent.gotoAnd', text):
        raise ValueError(f'{location}: unsupported complete form frame block')
    return None
