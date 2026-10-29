"""Chad s76 discriminator only; never replace the authored call or goto."""
import hashlib
import json
import re
from pathlib import Path

HANDLER = 'DefineSprite_607/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'
CALLEE = 'DefineSprite_16/frame_1/DoAction.as'
CALLEE_SHA256 = '1dfcec5ad005fbbba48c991ae1f0f4aa4884b35dc2a980e166d10f7d0e3c4e50'


def validate_case(path):
    expected = Path(__file__).resolve().parents[2] / 'evidence/sampling-upgrade/s76/chad__attack__neutral__ground__near.json'
    if path is None or json.loads(Path(path).read_text()) != json.loads(expected.read_text()):
        raise ValueError('Chad lifecycle requires the unchanged s76 attack case')


def event(phase):
    return f'_global.bvnChadObserve("{phase}", this);'


def instrument(original, updated, name, path):
    if name != 'fighter/chad':
        return updated
    if path == HANDLER:
        # The existing call-site instrumenter has already checked the exact body.
        needle = '      doAllAction();'
        if updated.count(needle) != 1:
            raise ValueError('missing unique Chad call')
        return updated.replace(needle, event('caller_before') + '\n' + needle + '\n' + event('caller_after'))
    if path != CALLEE:
        return updated
    normalized = original.replace('\r\n', '\n')
    if hashlib.sha256(normalized.encode()).hexdigest() != CALLEE_SHA256:
        raise ValueError('changed Chad lifecycle callee source')
    match = re.search(r'function doAllAction\(special\)\s*\{.*?^\}', updated, re.M | re.S)
    if match is None:
        raise ValueError('missing Chad doAllAction body')
    body = match[0]
    needle = '      _parent.gotoAndPlay("砍1");'
    if body.count(needle) != 1 or re.search(r'\breturn\b', body):
        raise ValueError('changed Chad goto or exit structure')
    body = body.replace(needle, event('goto_before') + '\n' + needle + '\n' + event('goto_after'))
    opening = body.index('{') + 1
    body = body[:opening] + '\n' + event('callee_enter') + body[opening:-1] + '\n' + event('callee_exit') + '\n}'
    return updated[:match.start()] + body + updated[match.end():]
