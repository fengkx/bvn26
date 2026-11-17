"""Compile solid paint from directed source edges, never from shape bounds."""
from __future__ import annotations

import copy
import xml.etree.ElementTree as ET

from bitmap_shape_polygon import bitmap_shape_fill_polygons


def solid_fill_polygons(shape: ET.Element):
    geometry = copy.deepcopy(shape)
    for style in geometry.findall('.//fillStyles/item'):
        style.attrib.pop('bitmapId', None)
        if style.get('fillStyleType') == '0':
            style.set('bitmapId', '0')
    for record in geometry.findall('./shapes/shapeRecords/item'):
        if record.get('type') == 'StyleChangeRecord':
            record.set('stateLineStyle', 'false')
    return bitmap_shape_fill_polygons(geometry)


def solid_closed_strokes(shape: ET.Element):
    styles = shape.findall('./shapes/lineStyles/lineStyles2/item')
    if not styles:
        return None
    # Non-scaling strokes, other caps/joins and gradient strokes need their own
    # source-backed renderer; this path retains ordinary round closed strokes.
    for style in styles:
        if (style.get('hasFillFlag') != 'false' or style.get('startCapStyle') != '0'
                or style.get('endCapStyle') != '0' or style.get('joinStyle') != '0'
                or any(style.get(key) == 'true' for key in
                       ('noClose', 'noHScaleFlag', 'noVScaleFlag', 'pixelHintingFlag'))):
            return None
    geometry = copy.deepcopy(shape)
    fills = geometry.find('./shapes/fillStyles/fillStyles')
    if fills is None:
        return None
    fills.clear()
    for _ in styles:
        ET.SubElement(fills, 'item', bitmapId='0')
    for record in geometry.findall('./shapes/shapeRecords/item'):
        if record.get('type') != 'StyleChangeRecord':
            continue
        if record.get('stateNewStyles') == 'true':
            return None
        record.set('stateFillStyle0', 'true')
        record.set('fillStyle0', '0')
        record.set('stateFillStyle1', record.get('stateLineStyle', 'false'))
        record.set('fillStyle1', record.get('lineStyle', '0'))
        record.set('stateLineStyle', 'false')
    paths = bitmap_shape_fill_polygons(geometry)
    if paths is None:
        return None
    return [{'width': int(style.get('width', 0)) / 20,
             'color': {key: int(style.find('color').get(key, '255' if key == 'alpha' else '0'))
                       for key in ('red', 'green', 'blue', 'alpha')},
             'paths': contours}
            for style, contours in zip(styles, paths)]
