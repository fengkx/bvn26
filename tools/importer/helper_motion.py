"""Compile position assignments from the original helper root and placed clips."""
import re


def compile_warp(source):
    """Resolve each source branch once using its incoming facing."""
    text = " ".join(source.split())
    branch = re.fullmatch(r"if\(_xscale ([<>]) 0\) \{ (.+?) \} else \{ (.+?) \}(?: (.+))?", text)
    if not branch:
        return None
    cases = {}
    for facing, body in zip((1, -1) if branch[1] == ">" else (-1, 1), branch.group(2, 3)):
        assignments = {}
        for line in (body + " " + (branch[4] or "")).strip().split(";"):
            line = line.strip()
            if not line:
                continue
            pos = re.fullmatch(r'_([XY]) = _root\.game\["p" \+ pn\]\._([xy])(?: ([+-]) (\d+))?', line)
            turn = re.fullmatch(r'_xscale = (-?100)', line)
            if pos and pos[1].lower() == pos[2]:
                assignments[pos[2]] = int(pos[4] or 0) * (-1 if pos[3] == "-" else 1)
            elif turn:
                assignments["facing"] = int(turn[1]) // 100
            else:
                return None
        cases[str(facing)] = assignments
    return {"op": "warp_by_facing", "cases": cases}


def compile_clip(source):
    text = " ".join(source.split())
    motion = re.fullmatch(r'onClipEvent\(enterFrame\)\{ if\(_parent\._xscale < 0\) \{ _parent\._x -= (\d+); \} else \{ _parent\._x \+= \1; \}(?: _parent\._y -= (\d+);)? \}', text)
    if motion:
        return {"op": "move_owner", "forward": int(motion[1]), "vertical": -int(motion[2] or 0)}
    vertical = re.fullmatch(r'onClipEvent\(enterFrame\)\{ _parent\._y \+= (\d+); \}', text)
    if vertical:
        return {"op": "move_owner", "forward": 0, "vertical": int(vertical[1])}
    if text == 'onClipEvent(enterFrame){ if(this.hitTest(_root.game["p" + _parent.pn].mc.bdmn)) { if(_root.game["p" + _parent.pn].mc.动作 == 2) { _root.game["p" + _parent.pn].mc.gotoAndPlay("被打"); } } }':
        return {"op": "restart_hurt_on_contact"}
    move = re.fullmatch(r'onClipEvent\(enterFrame\)\{ if\(_root\.zhanting == false\) \{ _X = _X \+ (\d+); \} \}', text)
    if move:
        return {"op": "move_clip", "speed": int(move[1])}
    if "if(played == 0)" in text and "gotoAndPlay(5);" in text:
        tests = re.findall(r'(hitmc\.)?hitTest\(_root\.game\["p" \+ _parent\.pn\]\.mc\.(\w+)\)', text)
        speed = re.search(r'_X = _X \+ (movspeed|\d+);', text)[1]
        return {"op": "projectile", "targets": [name for _, name in tests],
                "hitmc_targets": [name for prefix, name in tests if prefix],
                "keep_moving": speed != "movspeed", "speed": speed}
    return None
