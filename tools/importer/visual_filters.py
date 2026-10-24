"""Compile only filter families with a native display-object implementation."""
from __future__ import annotations
import math
from xml.etree.ElementTree import Element


def compile_filters(filters: Element, source: str) -> list[dict]:
    try:
        return _compile_filters(filters, source)
    except (ValueError, KeyError, TypeError) as error:
        if str(error).startswith(source + ':'):
            raise
        raise ValueError(f'{source}: malformed Flash filter: {error}') from error


def _compile_filters(filters: Element, source: str) -> list[dict]:
    if filters.attrib:
        raise ValueError(f'{source}: unsupported filter list fields: {sorted(filters.attrib)}')
    result = []
    for item in filters:
        kind = item.get('type')
        common = {'type', 'id'}
        allowed = {
            'BLURFILTER': common | {'blurX', 'blurY', 'passes', 'reserved'},
            'GLOWFILTER': common | {'blurX', 'blurY', 'passes', 'strength', 'innerGlow',
                                    'knockout', 'compositeSource'},
            'DROPSHADOWFILTER': common | {'blurX', 'blurY', 'passes', 'strength',
                'innerShadow', 'knockout', 'compositeSource', 'angle', 'distance'},
            'COLORMATRIXFILTER': common,
        }
        if item.tag != 'item' or kind not in allowed or set(item.attrib) - allowed[kind]:
            raise ValueError(f'{source}: unsupported Flash filter {kind}: {sorted(item.attrib)}')
        expected_id = {'BLURFILTER': '1', 'GLOWFILTER': '2', 'DROPSHADOWFILTER': '0', 'COLORMATRIXFILTER': '6'}[kind]
        if item.get('id', expected_id) != expected_id:
            raise ValueError(f'{source}: inconsistent {kind} id')
        if item.get('reserved', '0') != '0':
            raise ValueError(f'{source}: unsupported {kind} reserved bits')
        record = {'type': kind}
        if kind in ('BLURFILTER', 'GLOWFILTER', 'DROPSHADOWFILTER'):
            for field in ('blurX', 'blurY', 'passes'):
                if field not in item.attrib:
                    raise ValueError(f'{source}: {kind} requires {field}')
                value = float(item.attrib[field])
                if not math.isfinite(value) or not 0 <= value <= (15 if field == 'passes' else 255):
                    raise ValueError(f'{source}: unsupported {kind}.{field}={value}')
                if field == 'passes' and not value.is_integer():
                    raise ValueError(f'{source}: fractional filter passes {value}')
                record[field] = int(value) if field == 'passes' else value
        if kind in ('GLOWFILTER', 'DROPSHADOWFILTER'):
            inner_flag = 'innerGlow' if kind == 'GLOWFILTER' else 'innerShadow'
            color_field = 'glowColor' if kind == 'GLOWFILTER' else 'dropShadowColor'
            for flag, expected in ((inner_flag, 'false'), ('knockout', 'false'), ('compositeSource', 'true')):
                if item.get(flag) != expected:
                    raise ValueError(f'{source}: unsupported {kind}.{flag}={item.get(flag)}')
            color = item.find(color_field)
            if color is None:
                raise ValueError(f'{source}: {kind} requires {color_field}')
            if (set(color.attrib) - {'type', 'red', 'green', 'blue', 'alpha'}
                    or color.get('type', 'RGBA') != 'RGBA' or len(color)):
                raise ValueError(f'{source}: unsupported {kind}.{color_field} fields')
            channels = [int(color.attrib[k]) for k in ('red', 'green', 'blue', 'alpha')]
            if not all(0 <= channel <= 255 for channel in channels):
                raise ValueError(f'{source}: invalid {kind}.{color_field} channel')
            record['color'] = [channel / 255 for channel in channels]
            record['strength'] = float(item.attrib['strength'])
            if not math.isfinite(record['strength']) or not 0 <= record['strength'] <= 255:
                raise ValueError(f'{source}: invalid {kind} strength')
        if kind == 'DROPSHADOWFILTER':
            for field in ('angle', 'distance'):
                value = float(item.attrib[field])
                if not math.isfinite(value):
                    raise ValueError(f'{source}: non-finite {kind}.{field}')
                record[field] = value
        if kind == 'COLORMATRIXFILTER':
            matrix = item.find('matrix')
            if matrix is None or matrix.attrib or any(
                    v.tag != 'item' or v.attrib or len(v) for v in matrix):
                raise ValueError(f'{source}: unsupported ColorMatrixFilter matrix fields')
            values = [float(v.text) for v in item.findall('./matrix/item')]
            if len(values) != 20 or not all(math.isfinite(v) for v in values):
                raise ValueError(f'{source}: ColorMatrixFilter requires 20 finite values')
            record['matrix'] = values
        expected_children = {'BLURFILTER': set(), 'GLOWFILTER': {'glowColor'},
                             'DROPSHADOWFILTER': {'dropShadowColor'}, 'COLORMATRIXFILTER': {'matrix'}}[kind]
        if {child.tag for child in item} != expected_children or len(item) != len(expected_children):
            raise ValueError(f'{source}: unexpected {kind} child fields')
        result.append(record)
    return result
