"""Reject unsupported placement semantics and invalid numeric compiler inputs."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from xml.etree.ElementTree import Element


# These flags only affect SWF serialization or select an absent optional field.
# Active semantic flags must have an implementation below, never a default.
PLACEMENT_FIELDS = {
    'type', 'depth', 'characterId', 'name', 'ratio', 'clipDepth', 'blendMode', 'bitmapCache',
    'forceWriteAsLong', 'placeFlagMove', 'placeFlagHasCharacter',
    'placeFlagHasClipActions', 'placeFlagHasClipDepth', 'placeFlagHasColorTransform',
    'placeFlagHasMatrix', 'placeFlagHasName', 'placeFlagHasRatio',
    'placeFlagHasBlendMode', 'placeFlagHasCacheAsBitmap', 'placeFlagHasClassName',
    'placeFlagHasFilterList', 'placeFlagHasImage', 'placeFlagHasVisible',
    'placeFlagOpaqueBackground', 'reserved',
}
UNSUPPORTED_FLAGS = {
    'placeFlagHasClassName',
    'placeFlagHasImage', 'placeFlagHasVisible', 'placeFlagOpaqueBackground',
}
REQUIRED_ATTRIBUTES = {
    'placeFlagHasCharacter': 'characterId', 'placeFlagHasName': 'name',
    'placeFlagHasRatio': 'ratio', 'placeFlagHasClipDepth': 'clipDepth',
    'placeFlagHasBlendMode': 'blendMode', 'placeFlagHasCacheAsBitmap': 'bitmapCache',
}
REQUIRED_CHILDREN = {
    'placeFlagHasMatrix': 'matrix', 'placeFlagHasColorTransform': 'colorTransform',
    'placeFlagHasClipActions': 'clipActions', 'placeFlagHasFilterList': 'surfaceFilterList',
}


def finite_numbers(value, source: str) -> None:
    """JSON permits NaN/Infinity in Python; Godot must never receive them."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f'{source}: non-finite number {value!r}')
    if isinstance(value, dict):
        for key, child in value.items():
            finite_numbers(child, f'{source}/{key}')
    elif isinstance(value, list):
        for index, child in enumerate(value):
            finite_numbers(child, f'{source}/{index}')


def validate_placement(tag: Element, source: str) -> None:
    if tag.get('bitmapCache', '0') not in ('0', '1'):
        raise ValueError(f'{source}: unsupported bitmapCache={tag.get("bitmapCache")}')
    for name, value in tag.attrib.items():
        if name not in PLACEMENT_FIELDS:
            raise ValueError(f'{source}: unsupported PlaceObject field {name}={value}')
        if name in UNSUPPORTED_FLAGS and value != 'false':
            raise ValueError(f'{source}: unsupported PlaceObject field {name}={value}')
        if name.startswith('placeFlag') and value not in ('true', 'false'):
            raise ValueError(f'{source}: invalid PlaceObject flag {name}={value}')
    for flag, attribute in REQUIRED_ATTRIBUTES.items():
        if tag.get(flag) == 'true' and attribute not in tag.attrib:
            raise ValueError(f'{source}: {flag} requires {attribute}')
    for flag, child in REQUIRED_CHILDREN.items():
        if tag.get(flag) == 'true' and tag.find(child) is None:
            raise ValueError(f'{source}: {flag} requires {child}')
    for child in tag:
        if child.tag not in REQUIRED_CHILDREN.values():
            raise ValueError(f'{source}: unsupported PlaceObject child {child.tag}')
    for child_name, selectors in {
        'matrix': {'hasScale': ('scaleX', 'scaleY'),
                   'hasRotate': ('rotateSkew0', 'rotateSkew1')},
        'colorTransform': {'hasMultTerms': ('redMultTerm', 'greenMultTerm', 'blueMultTerm'),
                           'hasAddTerms': ('redAddTerm', 'greenAddTerm', 'blueAddTerm')},
    }.items():
        child = tag.find(child_name)
        if child is None:
            continue
        for flag, fields in selectors.items():
            if child.get(flag) == 'true':
                for field in fields:
                    if field not in child.attrib:
                        raise ValueError(f'{source}: {child_name}.{flag} requires {field}')
        for field, value in child.attrib.items():
            if field == 'type':
                expected = {'matrix': {'MATRIX'}, 'colorTransform': {'CXFORM', 'CXFORMWITHALPHA'}}
                if value not in expected[child_name]:
                    raise ValueError(f'{source}: invalid {child_name}.type={value}')
            elif field in ('hasScale', 'hasRotate', 'hasMultTerms', 'hasAddTerms'):
                if value not in ('true', 'false'):
                    raise ValueError(f'{source}: invalid {child_name}.{field}={value}')
            else:
                try:
                    number = float(value)
                except ValueError as error:
                    raise ValueError(f'{source}: invalid numeric {child_name}.{field}={value}') from error
                finite_numbers(number, f'{source}/{child_name}/{field}')


def allowed_frame_source(bundle: dict, path: str, source: str, form_frame: int) -> bool:
    """Admit exact reviewed source only within its recorded form and SWF hash."""
    policy = json.loads(Path(__file__).with_name('loud_fail_allowlist.json').read_text())
    for entry in policy['entries']:
        if not entry.get('reason') or not entry.get('evidence'):
            raise ValueError('Import allowlist requires a reason and evidence')
        if (entry['swf'] == bundle['game_file'] and
                entry['swf_sha256'] == bundle['swf_sha256'] and
                entry['path'] == path and entry['form_frame'] == form_frame and
                entry['source_sha256'] == hashlib.sha256(source.encode()).hexdigest()):
            return True
    return False
