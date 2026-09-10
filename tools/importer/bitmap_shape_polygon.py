"""Retain single-contour bitmap fill boundaries instead of their bounding box."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET


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
