"""Compile only filter families with a native display-object implementation."""
from __future__ import annotations
import math
from xml.etree.ElementTree import Element


def compile_filters(filters: Element, source: str) -> list[dict]:
    result = []
    for item in filters:
        kind = item.get('type')
        common = {'type', 'id'}
        allowed = {
            'BLURFILTER': common | {'blurX', 'blurY', 'passes', 'reserved'},
            'GLOWFILTER': common | {'blurX', 'blurY', 'passes', 'strength', 'innerGlow',
                                    'knockout', 'compositeSource'},
            'COLORMATRIXFILTER': common,
        }
        if kind not in allowed or set(item.attrib) - allowed[kind]:
            raise ValueError(f'{source}: unsupported Flash filter {kind}: {sorted(item.attrib)}')
        record = {'type': kind}
        if kind in ('BLURFILTER', 'GLOWFILTER'):
            for field in ('blurX', 'blurY', 'passes'):
                if field not in item.attrib:
                    raise ValueError(f'{source}: {kind} requires {field}')
                value = float(item.attrib[field])
                if not math.isfinite(value) or not 0 <= value <= (15 if field == 'passes' else 255):
                    raise ValueError(f'{source}: unsupported {kind}.{field}={value}')
                if field == 'passes' and not value.is_integer():
                    raise ValueError(f'{source}: fractional filter passes {value}')
                record[field] = int(value) if field == 'passes' else value
        if kind == 'GLOWFILTER':
            for flag, expected in (('innerGlow', 'false'), ('knockout', 'false'), ('compositeSource', 'true')):
                if item.get(flag) != expected:
                    raise ValueError(f'{source}: unsupported GLOWFILTER.{flag}={item.get(flag)}')
            color = item.find('glowColor')
            if color is None:
                raise ValueError(f'{source}: GLOWFILTER requires glowColor')
            record['color'] = [int(color.attrib[k]) / 255 for k in ('red', 'green', 'blue', 'alpha')]
            record['strength'] = float(item.attrib['strength'])
            if not math.isfinite(record['strength']) or not 0 <= record['strength'] <= 255:
                raise ValueError(f'{source}: invalid glow strength')
        if kind == 'COLORMATRIXFILTER':
            values = [float(v.text) for v in item.findall('./matrix/item')]
            if len(values) != 20 or not all(math.isfinite(v) for v in values):
                raise ValueError(f'{source}: ColorMatrixFilter requires 20 finite values')
            record['matrix'] = values
        expected_children = {'BLURFILTER': set(), 'GLOWFILTER': {'glowColor'},
                             'COLORMATRIXFILTER': {'matrix'}}[kind]
        if {child.tag for child in item} != expected_children:
            raise ValueError(f'{source}: unexpected {kind} child fields')
        result.append(record)
    return result
