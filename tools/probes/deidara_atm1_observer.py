"""Observe the s64 helper stamp gap without assigning a source or instance ID."""
import hashlib
import json
from pathlib import Path

LOAD_PATH = 'frame_44/PlaceObject2_48_2/CLIPACTIONRECORD onClipEvent(load).as'
LOAD_SOURCE = 'game/fighter/fz/woailuo.swf#' + LOAD_PATH
LOAD_SHA256 = '171ac594ab7d5801eb6bd5ee84eeaaab865b3122c28a1ec5e2846e0a297e037f'


def validate_case(path):
    expected = Path(__file__).resolve().parents[2] / 'evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json'
    if path is None or json.loads(Path(path).read_text()) != json.loads(expected.read_text()):
        raise ValueError('atm1 provenance requires the unchanged s64 summon case')


def instrument_load(original, updated, name, path, *, stamp=False):
    if name != 'fighter/fz/woailuo' or path != LOAD_PATH:
        return updated
    if hashlib.sha256(original.replace('\r\n', '\n').encode()).hexdigest() != LOAD_SHA256:
        raise ValueError('changed Woailuo atm1 load source')
    opening = updated.index('{') + 1
    closing = updated.rfind('}')
    def event(phase):
        return f'\n_root.aiAtm1Observe("{phase}",this,"{LOAD_SOURCE}");\n'
    # Bind this authored placement, never the helper root or a name-only lookup.
    binding = f'\n_root.aiGeoStamp(this,"{LOAD_SOURCE}");\n' if stamp else ''
    return updated[:opening] + event('load_before') + updated[opening:closing] + binding + event('load_after') + updated[closing:]


def instrument_stamp(source):
    header = '_root.aiGeoStamp = function(mc, source)\n{'
    end = '\n};\n_root.aiGeoBox'
    if source.count(header) != 1 or source.count(end) != 1:
        raise ValueError('changed geometry stamp observer boundary')
    source = source.replace(header, header + '\n   _root.aiAtm1StampObserve("stamp_before",mc,source);', 1)
    return source.replace(end, '\n   _root.aiAtm1StampObserve("stamp_after",mc,source);' + end, 1)
