"""Measure a fixed affine smooth baseline on source-defined full-coverage interiors.

This extends no admitted sampler routing: mask edges are inventoried separately,
and this independently specified baseline must be rejected on any counterexample.
"""
import argparse
from collections import Counter
from fractions import Fraction
import json
import math
from pathlib import Path

from tools.probes.jinye_jpeg_source import decode as decode_source
from tools.probes.analyze_jinye_leaf_boundaries import decode as decode_native


def compose(left, right):
    a, b, c, d, tx, ty = left
    e, f, g, h, ux, uy = right
    return [a*e+c*f, b*e+d*f, a*g+c*h, b*g+d*h, a*ux+c*uy+tx, b*ux+d*uy+ty]


def transform(matrix, point):
    a, b, c, d, tx, ty = matrix
    x, y = point
    return a*x+c*y+tx, b*x+d*y+ty


def invert(matrix):
    a, b, c, d, tx, ty = matrix
    determinant = a*d-b*c
    if determinant == 0:
        raise ValueError("Singular source transform")
    return [d/determinant, -b/determinant, -c/determinant, a/determinant,
            (c*ty-d*tx)/determinant, (b*tx-a*ty)/determinant]


def inside(point, polygon):
    signs = []
    for first, second in zip(polygon, polygon[1:]+polygon[:1]):
        cross = (second[0]-first[0])*(point[1]-first[1])-(second[1]-first[1])*(point[0]-first[0])
        signs.append(cross)
    return all(value > 0 for value in signs) or all(value < 0 for value in signs)


def pixel_class(x, y, polygon):
    corners = [(x, y), (x+1, y), (x+1, y+1), (x, y+1)]
    if all(inside(point, polygon) for point in corners):
        return "interior"
    # The conservative polygon bounding box records coverage obligations without
    # choosing an edge algorithm from native opacity or color.
    if max(p[0] for p in polygon) < x or min(p[0] for p in polygon) > x+1 or max(p[1] for p in polygon) < y or min(p[1] for p in polygon) > y+1:
        return "outside"
    return "coverage_unproved"


def sample(source, coordinate):
    sx, sy = coordinate
    sx -= Fraction(1, 2)
    sy -= Fraction(1, 2)
    ix, iy = math.floor(sx), math.floor(sy)
    fx, fy = math.floor((sx-ix)*256), math.floor((sy-iy)*256)
    weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
    weights.append(256-sum(weights))
    pixels = [source[max(0, min(39, iy+dy))*92+max(0, min(91, ix+dx))]
              for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
    return [sum(weight*pixel[channel] for weight, pixel in zip(weights, pixels))//256 for channel in range(4)]


def compare_case(source, matrix, polygon, native, size=(600, 400)):
    inverse = invert(matrix)
    width, height = size
    assert len(native) == width*height
    counts = {"interior": 0, "outside": 0, "coverage_unproved": 0}
    native_support = dict.fromkeys(counts, 0)
    exact = active = active_exact = 0
    maxima = [0]*4
    deltas = [Counter() for _ in range(4)]
    failures = []
    bounds = (math.floor(min(p[0] for p in polygon))-1, math.floor(min(p[1] for p in polygon))-1,
              math.ceil(max(p[0] for p in polygon))+1, math.ceil(max(p[1] for p in polygon))+1)
    for y in range(height):
        for x in range(width):
            if x < bounds[0] or y < bounds[1] or x > bounds[2] or y > bounds[3]:
                counts["outside"] += 1
                native_support["outside"] += native[y*width+x][3] != 0
                continue
            classification = pixel_class(x, y, polygon)
            counts[classification] += 1
            native_support[classification] += native[y*width+x][3] != 0
            if classification != "interior":
                continue
            coordinate = transform(inverse, (x+Fraction(1, 2), y+Fraction(1, 2)))
            actual = sample(source, coordinate)
            target = native[y*width+x]
            exact += actual == target
            active += bool(actual[3] or target[3])
            active_exact += bool(actual[3] or target[3]) and actual == target
            maxima = [max(old, abs(a-b)) for old, a, b in zip(maxima, actual, target)]
            for channel, (a, b) in enumerate(zip(actual, target)):
                deltas[channel][a-b] += 1
            if actual != target:
                failures.append({"x": x, "y": y, "source_coordinate": list(map(str, coordinate)),
                                 "actual": actual, "native": target})
    assert sum(counts.values()) == width*height
    assert sum(native_support.values()) == sum(pixel[3] != 0 for pixel in native)
    return {"geometry_classes": counts, "interior_exact": exact,
            "native_nonzero_alpha_by_geometry": native_support,
            "nonzero_alpha_interior": active, "nonzero_alpha_interior_exact": active_exact,
            "max_channel_delta": maxima, "failures": failures,
            "signed_channel_delta_histograms": [dict(sorted(values.items())) for values in deltas],
            "baseline_admitted": False, "coverage_admitted": False, "production_admitted": False}


def source_geometry(spec, shape):
    source_to_stage = compose(compose(list(map(Fraction, spec["draw"])),
                                      list(map(Fraction, spec["outer"]))),
                              list(map(Fraction, spec["matrix"])))
    fill = shape["bitmap_matrix"]
    # FFDEC prints a rounded decimal for a signed 16.16 coefficient. Recover
    # that encoded integer before composing, retaining twip translations.
    fill_matrix = [Fraction(round(Fraction(fill.get(key, default))*65536), 65536*20)
                   for key, default in (("scaleX", "1"), ("rotateSkew0", "0"),
                                        ("rotateSkew1", "0"), ("scaleY", "1"))]
    fill_matrix += [Fraction(int(fill.get(key, "0")), 20) for key in ("translateX", "translateY")]
    records = shape["mask_records"]
    assert records[0]["type"] == "StyleChangeRecord" and records[0]["fillStyle1"] == "2"
    x, y = (int(records[0][key]) for key in ("moveDeltaX", "moveDeltaY"))
    points = [(Fraction(x, 20), Fraction(y, 20))]
    for record in records[1:-1]:
        assert record["type"] == "StraightEdgeRecord" and record["generalLineFlag"] == "true"
        x += int(record["deltaX"])
        y += int(record["deltaY"])
        points.append((Fraction(x, 20), Fraction(y, 20)))
    assert len(points) == 5 and points[0] == points[-1]
    return compose(source_to_stage, fill_matrix), [transform(source_to_stage, point) for point in points[:-1]]


def analyze(native, dump, output):
    fixture, captures, readbacks = decode_native(native)
    metadata, source = decode_source(dump, output / "decoded")
    results = []
    for capture in captures:
        spec = fixture["cases"][capture["source_case"]]
        shape = next(value for value in fixture["shapes"] if value["id"] == spec["shape"])
        matrix, polygon = source_geometry(spec, shape)
        results.append({"case": spec, "cached": capture["cached"],
                        "bitmap_to_stage": list(map(str, matrix)),
                        "stage_polygon": [list(map(str, point)) for point in polygon],
                        **compare_case(source, matrix, polygon, capture["pixels"])})
    return {"source": fixture["source"], "bitmap": metadata, "native_matrix_readbacks": readbacks,
            "baseline": "Exact affine inverse pixel center, 8-bit four-corner weights with residual fourth weight",
            "scope": "Fixed unadmitted affine baseline; no span routing inherited from axis-aligned controls",
            "cases": results, "baseline_admitted": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = analyze(args.native, args.dump, args.output)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    for case in result["cases"]:
        print(case["case"]["shape"], case["cached"], case["interior_exact"],
              case["geometry_classes"]["interior"], case["nonzero_alpha_interior_exact"],
              case["nonzero_alpha_interior"], case["max_channel_delta"])
