"""Test fixed affine smooth initializer hypotheses globally, without RGB routing."""
import argparse
from collections import Counter
from fractions import Fraction
import json
import math
from pathlib import Path

from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_jinye_smooth_leaf import compose, invert, source_geometry
from tools.probes.analyze_jinye_smooth_controls import interior_geometry
from tools.probes.decode_jinye_affine_controls import source_pixel
from tools.probes.decode_jinye_tag_controls import decode as decode_tags
from tools.probes.analyze_jinye_leaf_boundaries import decode as decode_leaves
from tools.probes.jinye_jpeg_source import decode as decode_jpeg


def inverse_rows(matrix):
    a, b, c, d, tx, ty = invert(matrix)
    return ((a, c, tx), (b, d, ty))


def fixed_rows(matrix, footprint):
    coefficients = inverse_rows(matrix)
    if footprint == "minimum":
        return tuple(tuple(row[:4]) for row in prepare(coefficients, "ties_even"))
    assert footprint == "center"
    rows = []
    for row in coefficients:
        a, b, tx = [math.floor(value*65536+Fraction(1, 2)) for value in row]
        rows.append((a, b, tx, round(Fraction(a+b, 2))))
    return tuple(rows)


def hypotheses(spec, shape):
    direct, polygon = source_geometry(spec, shape)
    # This is a named transfer hypothesis, not an admitted compound-fill rule.
    # Older controls independently consume child and draw translations; retain
    # their sequence globally before composing the unchanged source fill.
    consumed_spec = dict(spec)
    child = compose(list(map(Fraction, spec["outer"])), list(map(Fraction, spec["matrix"])))
    child[4:] = [Fraction(round(value*4), 4) for value in child[4:]]
    draw = list(map(Fraction, spec["draw"]))
    draw[4:] = [Fraction(math.trunc(value*4), 4) for value in draw[4:]]
    consumed_spec.update(matrix=child, outer=[1, 0, 0, 1, 0, 0], draw=draw)
    consumed, _ = source_geometry(consumed_spec, shape)
    return {f"{translation}/{footprint}": fixed_rows(matrix, footprint)
            for translation, matrix in (("declared", direct), ("legacy_child_draw_quarters", consumed))
            for footprint in ("center", "minimum")}, direct, polygon


def sample_fixed(source, rows, x, y, order):
    sx, sy = [a*x+b*y+t+offset-32768 for a, b, t, offset in rows]
    ix, iy = sx//65536, sy//65536
    fx, fy = (sx % 65536)//256, (sy % 65536)//256
    pixels = [source[max(0, min(39, iy+dy))*92+max(0, min(91, ix+dx))]
              for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
    if order == "byte_weights":
        weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
        weights.append(256-sum(weights))
        return [sum(w*p[k] for w, p in zip(weights, pixels))//256 for k in range(4)]
    assert order == "vertical_horizontal"
    left = [(pixels[0][k]*(256-fy)+pixels[2][k]*fy)//256 for k in range(4)]
    right = [(pixels[1][k]*(256-fy)+pixels[3][k]*fy)//256 for k in range(4)]
    return [(left[k]*(256-fx)+right[k]*fx)//256 for k in range(4)]


def compare(source, spec, shape, target, size):
    models, direct, polygon = hypotheses(spec, shape)
    geometry, samples = interior_geometry(tuple(direct), tuple(polygon), tuple(size))
    results = {}
    for name, rows in models.items():
        for order in ("byte_weights", "vertical_horizontal"):
            key = name+"/"+order
            exact = active = active_exact = 0
            histograms = [Counter() for _ in range(4)]
            failures = []
            for x, y, _ in samples:
                actual = sample_fixed(source, rows, x, y, order)
                native = target[y*size[0]+x]
                equal = actual == native
                exact += equal
                support = any(actual[:3]) or any(native[:3])
                active += support
                active_exact += support and equal
                for histogram, a, b in zip(histograms, actual, native):
                    histogram[a-b] += 1
                if not equal:
                    failures.append([x, y, actual, native])
            results[key] = {"samples": len(samples), "exact": exact,
                            "nonzero_rgb_union": active, "nonzero_rgb_union_exact": active_exact,
                            "signed_rgba_delta_histograms": [dict(sorted(h.items())) for h in histograms],
                            "max_channel_delta": [max(map(abs, h), default=0) for h in histograms],
                            "fixed_rows": rows, "failures": failures}
    return {"geometry_classes": geometry, "models": results}


def analyze(native, leaf_native, dump, output):
    fixture, sources, captures, _ = decode_tags(native)
    generated = [[source_pixel(index, x, y) for y in range(40) for x in range(92)] for index in range(6)]
    assert generated == sources
    controls = []
    for capture in captures:
        spec = fixture["cases"][capture["source_case"]]
        shape = next(row for row in fixture["source_graph"]["shapes"] if row["id"] == spec["shape"])
        controls.append({"case": spec["id"], "shape": spec["shape"], "source": spec["source"],
                         "scale": spec["draw"][0], "cached": capture["cached"],
                         **compare(generated[spec["source"]], spec, shape, capture["pixels"], (96, 96))})
    leaf_fixture, leaf_captures, _ = decode_leaves(leaf_native)
    decoder, pixels = decode_jpeg(dump, output/"decoded")
    leaves = []
    for capture in leaf_captures:
        spec = leaf_fixture["cases"][capture["source_case"]]
        shape = next(row for row in leaf_fixture["shapes"] if row["id"] == spec["shape"])
        leaves.append({"case": spec["id"], "shape": spec["shape"], "cached": capture["cached"],
                       **compare(pixels, spec, shape, capture["pixels"], (600, 400))})
    totals = {}
    for family, cases in (("independent_controls", controls), ("source_jpeg_leaves", leaves)):
        totals[family] = {}
        for model in cases[0]["models"]:
            scores = [case["models"][model] for case in cases]
            totals[family][model] = {"exact": sum(row["exact"] for row in scores),
                                     "samples": sum(row["samples"] for row in scores),
                                     "max_channel_delta": [max(row["max_channel_delta"][k] for row in scores) for k in range(4)]}
    return {"controls": controls, "leaves": leaves, "decoder": decoder, "totals": totals,
            "routing": "Every model is global across source, scale, cache state, and every original geometry interior",
            "cache_local_rebase_tested": False,
            "compound_fill_quarter_consumption_proved": False,
            "candidate_admitted": False, "gpu_advance_allowed": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--leaf-native", type=Path, required=True)
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = analyze(args.native, args.leaf_native, args.dump, args.output)
    (args.output/"analysis.json").write_text(json.dumps(result, separators=(",", ":"))+"\n")
    print(json.dumps(result["totals"], indent=2))
