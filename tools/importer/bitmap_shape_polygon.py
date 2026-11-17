"""Retain single-contour bitmap fill boundaries instead of their bounding box."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET


def adjacent_fill_boundary(contours: list) -> list | None:
    """Join exactly shared reversed edges; reject overlaps, holes and islands.

    Mask colors do not separate adjacent filled regions. Internal authored
    edges cancel, but unrelated/intersecting contours need a full union engine.
    """
    edges = {}
    joined = False
    for contour in contours:
        points = [tuple(point) for point in contour]
        for start, end in zip(points, points[1:] + points[:1]):
            if (start, end) in edges:
                return None
            if (end, start) in edges:
                del edges[end, start]
                joined = True
            else:
                edges[start, end] = True
    if not joined or not edges:
        return None
    following = {}
    for start, end in edges:
        if start in following:
            return None
        following[start] = end
    start = next(iter(following))
    boundary = []
    point = start
    while point in following:
        boundary.append(list(point))
        point = following.pop(point)
    if point != start or following or len(boundary) < 3:
        return None
    def side(a, b, p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])

    segments = list(zip(boundary, boundary[1:] + boundary[:1]))
    for i, (a, b) in enumerate(segments):
        for j in range(i + 1, len(segments)):
            if j == i + 1 or (i == 0 and j == len(segments) - 1):
                continue
            c, d = segments[j]
            if (max(a[0], b[0]) < min(c[0], d[0]) or max(c[0], d[0]) < min(a[0], b[0])
                    or max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1])):
                continue
            if side(a, b, c) * side(a, b, d) <= 0 and side(c, d, a) * side(c, d, b) <= 0:
                return None
    return boundary


def shape_fill_edges(shape: ET.Element, style_indices: dict[int, int]) -> list | None:
    """Decode directed fill edges with the source style-table ownership."""
    initial_styles = shape.findall('./shapes/fillStyles/fillStyles/item')
    fill_base = 0
    active_style_count = len(initial_styles)
    current_fill0 = 0
    current_fill1 = 0
    x = y = 0
    edges: list[list[tuple[tuple[int, int], tuple[int, int], list[tuple[int, int]]]]] = [
        [] for _ in style_indices
    ]

    def append_edge(points: list[tuple[int, int]]) -> bool:
        if len(points) < 2:
            return False
        start, end = points[0], points[-1]
        if current_fill0:
            global_style = fill_base + current_fill0
            output_style = style_indices.get(global_style)
            if output_style is not None:
                edges[output_style].append((end, start, list(reversed(points))))
        if current_fill1:
            global_style = fill_base + current_fill1
            output_style = style_indices.get(global_style)
            if output_style is not None:
                edges[output_style].append((start, end, points))
        return True

    for record in shape.findall('./shapes/shapeRecords/item'):
        kind = record.get('type')
        if kind == 'StyleChangeRecord':
            if record.get('stateNewStyles') == 'true':
                # Keep NewStyles scoped only where the source explicitly resets
                # both active fills before drawing with the new style table.
                if (
                    record.get('stateFillStyle0') != 'true'
                    or record.get('stateFillStyle1') != 'true'
                    or int(record.get('fillStyle0', -1)) != 0
                    or int(record.get('fillStyle1', -1)) != 0
                ):
                    return None
                new_styles = record.findall('./fillStyles/fillStyles/item')
                fill_base += active_style_count
                active_style_count = len(new_styles)
                # New fill-style indices start at one in the new style array.
                if not new_styles:
                    return None
            if record.get('stateMoveTo') == 'true':
                x = int(record.get('moveDeltaX', 0))
                y = int(record.get('moveDeltaY', 0))
            if record.get('stateFillStyle0') == 'true':
                current_fill0 = int(record.get('fillStyle0', 0))
            if record.get('stateFillStyle1') == 'true':
                current_fill1 = int(record.get('fillStyle1', 0))
            if record.get('stateLineStyle') == 'true' and int(record.get('lineStyle', 0)):
                return None
            continue

        if kind == 'StraightEdgeRecord':
            nx = x + int(record.get('deltaX', 0))
            ny = y + int(record.get('deltaY', 0))
            points = [(x, y), (nx, ny)]
        elif kind == 'CurvedEdgeRecord':
            cx = x + int(record.get('controlDeltaX', 0))
            cy = y + int(record.get('controlDeltaY', 0))
            nx = cx + int(record.get('anchorDeltaX', 0))
            ny = cy + int(record.get('anchorDeltaY', 0))
            steps = max(1, math.ceil(math.sqrt(math.hypot(x - 2 * cx + nx, y - 2 * cy + ny) / 4)))
            points = [
                (round((1-t)**2*x + 2*(1-t)*t*cx + t*t*nx),
                 round((1-t)**2*y + 2*(1-t)*t*cy + t*t*ny))
                for t in (step / steps for step in range(steps + 1))
            ]
        elif kind == 'EndShapeRecord':
            break
        else:
            return None
        if not append_edge(points):
            return None
        x, y = nx, ny

    return edges


def bitmap_shape_fill_polygons(shape: ET.Element) -> list[list[list[list[float]]]] | None:
    """Compile simple, closed SWF bitmap fill contours, one entry per bitmap fill.

    SWF edges can border two fills. fillStyle1 follows the recorded edge and
    fillStyle0 uses it in reverse, so each fill gets its own directed contour.
    Unsupported/open/ambiguous geometry returns None and keeps the legacy
    bounding-box renderer instead of inventing a mask.
    """
    style_items = shape.findall('.//fillStyles/item')
    bitmap_style_indices: dict[int, int] = {}
    placeholder_indices: set[int] = set()
    for style_index, item in enumerate(style_items, 1):
        if 'bitmapId' in item.attrib:
            if int(item.attrib['bitmapId']) == 65535:
                placeholder_indices.add(len(bitmap_style_indices))
            bitmap_style_indices[style_index] = len(bitmap_style_indices)
    if not bitmap_style_indices:
        return None

    edges = shape_fill_edges(shape, bitmap_style_indices)
    if edges is None:
        return None

    output: list[list[list[list[float]]]] = []
    for fill_index, fill_edges in enumerate(edges):
        # SWF's no-bitmap sentinel and unused styles paint nothing. Preserve
        # their slots so later masks still address the original fill table.
        if fill_index in placeholder_indices or not fill_edges:
            output.append([])
            continue
        contours: list[list[tuple[int, int]]] = []
        unused = list(fill_edges)
        while unused:
            first = unused.pop(0)
            contour = list(first[2])
            start, end = first[0], first[1]
            while end != start:
                next_edges = [i for i, edge in enumerate(unused) if edge[0] == end]
                if len(next_edges) != 1:
                    return None
                edge = unused.pop(next_edges[0])
                contour.extend(edge[2][1:])
                end = edge[1]
                if len(contour) > len(fill_edges) * 64 + 2:
                    return None
            if len(contour) < 4 or contour[0] != contour[-1]:
                return None
            contour.pop()
            if len(set(contour)) != len(contour):
                return None
            contours.append(contour)
        # Polygon2D can draw disjoint contours, but not holes. Refuse nested
        # contours until a fill-rule-aware tessellator is available.
        for i, contour in enumerate(contours):
            for j, other in enumerate(contours):
                if i != j and _point_in_polygon(contour[0], other):
                    return None
        output.append([[[x / 20, y / 20] for x, y in contour] for contour in contours])
    return output


def _point_in_polygon(point: tuple[int, int], polygon: list[tuple[int, int]]) -> bool:
    x, y = point
    inside = False
    previous = polygon[-1]
    for current in polygon:
        x0, y0 = previous
        x1, y1 = current
        if (y0 > y) != (y1 > y):
            cross = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)
            if (cross < 0) == (y1 < y0):
                inside = not inside
        previous = current
    return inside


def bitmap_shape_polygon(shape: ET.Element) -> list[list[float]] | None:
    fills = shape.findall('./shapes/fillStyles/fillStyles/item')
    if len(fills) != 1 or 'bitmapId' not in fills[0].attrib:
        return None
    points = []
    x = y = 0
    curved = False
    for record in shape.findall('./shapes/shapeRecords/item'):
        kind = record.get('type')
        if kind == 'StyleChangeRecord':
            if record.get('stateNewStyles') == 'true':
                return None
            if record.get('stateMoveTo') == 'true':
                if points:
                    return None  # Multiple contours need fill-rule-aware tessellation.
                x = int(record.get('moveDeltaX', 0))
                y = int(record.get('moveDeltaY', 0))
                points.append([x / 20, y / 20])
            for side in (0, 1):
                if int(record.get(f'fillStyle{side}', 0)) not in (0, 1):
                    return None
            if record.get('stateLineStyle') == 'true':
                return None
        elif kind == 'StraightEdgeRecord':
            x += int(record.get('deltaX', 0))
            y += int(record.get('deltaY', 0))
            points.append([x / 20, y / 20])
        elif kind == 'CurvedEdgeRecord':
            curved = True
            cx = x + int(record.get('controlDeltaX', 0))
            cy = y + int(record.get('controlDeltaY', 0))
            ex = cx + int(record.get('anchorDeltaX', 0))
            ey = cy + int(record.get('anchorDeltaY', 0))
            # Quadratic chord error <= |P0 - 2P1 + P2| / (4 n²).
            # One twip (0.05 source pixels) bounds the tessellation error.
            steps = max(1, math.ceil(math.sqrt(math.hypot(x - 2 * cx + ex, y - 2 * cy + ey) / 4)))
            for step in range(1, steps + 1):
                t = step / steps
                points.append([((1-t)**2*x + 2*(1-t)*t*cx + t*t*ex) / 20,
                               ((1-t)**2*y + 2*(1-t)*t*cy + t*t*ey) / 20])
            x, y = ex, ey
        elif kind != 'EndShapeRecord':
            return None
    if len(points) < 4 or points[0] != points[-1]:
        return None
    points.pop()
    if len({tuple(point) for point in points}) != len(points):
        return None  # Touching contours also need fill-rule-aware tessellation.
    # Keep the existing rectangle fast path.
    if not curved and len(points) == 4 and all(
        a[0] == b[0] or a[1] == b[1]
        for a, b in zip(points, points[1:] + points[:1])
    ):
        return None
    return points
