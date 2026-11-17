"""Compile solid paint from directed source edges, never from shape bounds."""
from __future__ import annotations

import copy
from collections import Counter
import xml.etree.ElementTree as ET

from bitmap_shape_polygon import bitmap_shape_fill_polygons, shape_fill_edges


def solid_fill_meshes(shape: ET.Element):
    """Tessellate complex source fills, retaining holes and shared junctions."""
    from shapely import constrained_delaunay_triangles, node, polygonize
    from shapely.geometry import MultiLineString

    geometry = copy.deepcopy(shape)
    styles = {index: slot for slot, index in enumerate(
        index for index, style in enumerate(geometry.findall('.//fillStyles/item'), 1)
        if style.get('fillStyleType') == '0')}
    for record in geometry.findall('./shapes/shapeRecords/item'):
        if record.get('type') == 'StyleChangeRecord':
            record.set('stateLineStyle', 'false')
    edges = shape_fill_edges(geometry, styles)
    if edges is None:
        return None
    winding_rule = shape.get('usesFillWindingRule') == 'true'
    output = []
    for fill_edges in edges:
        balance = Counter()
        for start, end, _ in fill_edges:
            balance[start] += 1
            balance[end] -= 1
        if any(balance.values()):
            return None
        segments = [(a, b) for _, _, points in fill_edges
                    for a, b in zip(points, points[1:]) if a != b]
        vertices, indices, triangles = [], {}, []
        if segments:
            # Node the linework before polygonizing: a source fill may have
            # several outgoing edges at one vertex, or nested hole contours.
            faces = polygonize(node(MultiLineString(segments)).geoms)
            for face in faces.geoms:
                point = face.representative_point()
                winding = _winding_number(point.x, point.y, segments)
                if not (winding != 0 if winding_rule else winding % 2 != 0):
                    continue
                for triangle in constrained_delaunay_triangles(face).geoms:
                    triangle_indices = []
                    for x, y in list(triangle.exterior.coords)[:-1]:
                        key = (x, y)
                        if key not in indices:
                            indices[key] = len(vertices)
                            vertices.append([x / 20, y / 20])
                        triangle_indices.append(indices[key])
                    triangles.append(triangle_indices)
        output.append({'vertices': vertices, 'triangles': triangles})
    return output


def _winding_number(x, y, segments):
    winding = 0
    for (x0, y0), (x1, y1) in segments:
        side = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)
        if y0 <= y < y1 and side > 0:
            winding += 1
        elif y1 <= y < y0 and side < 0:
            winding -= 1
    return winding


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
