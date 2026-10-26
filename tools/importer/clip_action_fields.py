"""Preserve clip event metadata or reject fields the timeline cannot represent.

This validates serialization, not ownership of the ActionScript event body. A
hash and event name are evidence for the separate body/controller compiler.
"""
from xml.etree.ElementTree import Element

EVENT_FIELDS = frozenset('clipEvent' + name for name in (
    'Construct', 'Data', 'DragOut', 'DragOver', 'EnterFrame', 'Initialize',
    'KeyDown', 'KeyPress', 'KeyUp', 'Load', 'MouseDown', 'MouseMove', 'MouseUp',
    'Press', 'Release', 'ReleaseOutside', 'RollOut', 'RollOver', 'Unload'))


def _fields(element: Element, allowed: set, source: str) -> None:
    expected_type = {'clipActions': 'CLIPACTIONS', 'allEventFlags': 'CLIPEVENTFLAGS',
                     'eventFlags': 'CLIPEVENTFLAGS', 'item': 'CLIPACTIONRECORD'}.get(element.tag)
    if 'type' in element.attrib and element.get('type') != expected_type:
        raise ValueError(f'{source}: invalid {element.tag}.type={element.get("type")}')
    unknown = set(element.attrib) - allowed
    if unknown:
        raise ValueError(f'{source}: unsupported {element.tag} fields {sorted(unknown)}')


def _events(element: Element, source: str) -> set[str]:
    _fields(element, EVENT_FIELDS | {'type', 'reserved', 'reserved2'}, source)
    if len(element):
        raise ValueError(f'{source}: unexpected child in {element.tag}')
    for key, value in element.attrib.items():
        if key in EVENT_FIELDS and value not in ('true', 'false'):
            raise ValueError(f'{source}: invalid {key}={value}')
        if key in ('reserved', 'reserved2') and value != '0':
            raise ValueError(f'{source}: unsupported {element.tag}.{key}={value}')
    return {key for key in EVENT_FIELDS if element.get(key) == 'true'}


def validate_clip_actions(actions: Element, source: str) -> None:
    _fields(actions, {'type', 'reserved'}, source)
    if actions.get('reserved', '0') != '0':
        raise ValueError(f'{source}: unsupported clipActions.reserved')
    if [child.tag for child in actions] != ['allEventFlags', 'clipActionRecords']:
        raise ValueError(f'{source}: clipActions requires allEventFlags and clipActionRecords')
    declared = _events(actions.find('allEventFlags'), source)
    records = actions.find('clipActionRecords')
    _fields(records, set(), source)
    observed = set()
    for index, record in enumerate(records):
        location = f'{source}/clipActionRecords/{index}'
        if record.tag != 'item' or [child.tag for child in record] != ['eventFlags']:
            raise ValueError(f'{location}: clip action requires one eventFlags')
        _fields(record, {'type', 'actionBytes', 'keyCode'}, location)
        events = _events(record.find('eventFlags'), location)
        if not events:
            raise ValueError(f'{location}: clip action has no event')
        # The current timeline carries events and code hashes, but not keyCode.
        # Accepting this event would lose the key even with an empty action body.
        if 'clipEventKeyPress' in events or record.get('keyCode', '0') != '0':
            raise ValueError(f'{location}: unsupported clip action keyCode/KeyPress')
        encoded = record.get('actionBytes', '')
        if not encoded or len(encoded) % 2 or any(c not in '0123456789abcdefABCDEF' for c in encoded):
            raise ValueError(f'{location}: invalid clip action actionBytes')
        observed.update(events)
    if declared != observed:
        raise ValueError(f'{source}: clip action allEventFlags differs from records')
