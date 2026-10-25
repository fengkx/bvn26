"""Reject fixed affine smooth constructions using independent ramps and impulses."""
import argparse
from collections import Counter
from fractions import Fraction
from functools import lru_cache
import json
import math
from pathlib import Path

from tools.probes.analyze_jinye_smooth_leaf import invert, pixel_class, sample, source_geometry, transform
from tools.probes.decode_jinye_affine_controls import decode, source_pixel


def separable_sample(source, coordinate):
    sx, sy = [value-Fraction(1, 2) for value in coordinate]
    ix, iy = math.floor(sx), math.floor(sy)
    fx, fy = math.floor((sx-ix)*256), math.floor((sy-iy)*256)
    pixels = [source[max(0, min(39, iy+dy))*92+max(0, min(91, ix+dx))]
              for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
    left = [(pixels[0][k]*(256-fy)+pixels[2][k]*fy)//256 for k in range(4)]
    right = [(pixels[1][k]*(256-fy)+pixels[3][k]*fy)//256 for k in range(4)]
    return [(left[k]*(256-fx)+right[k]*fx)//256 for k in range(4)]


@lru_cache(maxsize=6)
def interior_geometry(matrix, polygon, size):
    inverse = invert(matrix)
    width, height = size
    counts = Counter()
    samples = []
    for y in range(height):
        for x in range(width):
            classification = pixel_class(x, y, polygon)
            counts[classification] += 1
            if classification == "interior":
                samples.append((x, y, transform(inverse, (x+Fraction(1, 2), y+Fraction(1, 2)))))
    assert sum(counts.values()) == width*height
    return dict(counts), samples


def score(source, matrix, polygon, target, ramp_axis=None, ramp_step=None, size=(96, 96)):
    width, height = size
    assert len(target) == width*height
    counts, samples = interior_geometry(tuple(matrix), tuple(polygon), tuple(size))
    rules = {name: {"samples": 0, "exact": 0, "max_channel_delta": [0]*4,
                    "nonzero_rgb_union": 0, "nonzero_rgb_union_exact": 0,
                    "signed_channel_delta_histograms": [Counter() for _ in range(4)], "failures": []}
             for name in ("four_corner_byte_weights", "vertical_then_horizontal")}
    intervals = []
    alpha_histogram = Counter()
    for x, y, coordinate in samples:
        native = target[y*width+x]
        alpha_histogram[native[3]] += 1
        predictions = {"four_corner_byte_weights": sample(source, coordinate),
                       "vertical_then_horizontal": separable_sample(source, coordinate)}
        for name, actual in predictions.items():
            result = rules[name]
            result["samples"] += 1
            result["exact"] += actual == native
            active = any(actual[:3]) or any(native[:3])
            result["nonzero_rgb_union"] += active
            result["nonzero_rgb_union_exact"] += active and actual == native
            delta = [a-b for a, b in zip(actual, native)]
            result["max_channel_delta"] = [max(old, abs(value)) for old, value in zip(result["max_channel_delta"], delta)]
            for histogram, value in zip(result["signed_channel_delta_histograms"], delta):
                histogram[value] += 1
            if actual != native:
                result["failures"].append({"x": x, "y": y, "actual": actual, "native": native})
        if ramp_axis is not None:
            assert ramp_axis in (0, 1) and ramp_step > 0
            # Conditional only: if the final channel is floor(step*centroid),
            # readback constrains that centroid. It does not choose a renderer.
            lo = Fraction(native[ramp_axis], ramp_step)
            hi = Fraction(native[ramp_axis]+1, ramp_step)
            ideal = coordinate[ramp_axis]-Fraction(1, 2)
            intervals.append({"x": x, "y": y, "native_channel": native[ramp_axis],
                              "native_alpha": native[3], "lower_inclusive": str(lo),
                              "opaque_centroid_constraint": native[3] == 255,
                              "upper_exclusive": str(hi), "ideal_inverse_center": str(ideal),
                              "contains_ideal": lo <= ideal < hi})
    for result in rules.values():
        result["signed_channel_delta_histograms"] = [dict(sorted(histogram.items())) for histogram in result["signed_channel_delta_histograms"]]
    return {"geometry_classes": dict(counts), "fixed_constructions": rules,
            "native_interior_alpha_histogram": dict(sorted(alpha_histogram.items())),
            "conditional_ramp_centroid_intervals": intervals,
            "centroid_contains_ideal": sum(row["contains_ideal"] for row in intervals),
            "centroid_total": len(intervals), "sampler_admitted": False, "production_admitted": False}


def analyze(native):
    fixture, sources, captures, matrices = decode(native)
    generated_sources = [[source_pixel(index, x, y) for y in range(40) for x in range(92)] for index in range(6)]
    assert sources == generated_sources
    results = []
    for capture in captures:
        spec = fixture["cases"][capture["source_case"]]
        shape = next(row for row in fixture["source_graph"]["shapes"] if row["id"] == spec["shape"])
        matrix, polygon = source_geometry(spec, shape)
        source_id = spec["source"]
        result = score(generated_sources[source_id], matrix, polygon, capture["pixels"],
                       ramp_axis=source_id if source_id in (0, 1) else None,
                       ramp_step=(2, 6)[source_id] if source_id in (0, 1) else None)
        results.append({"source_case": spec["id"], "shape": spec["shape"], "source": source_id,
                        "draw_scale": spec["draw"][0], "cached": capture["cached"], **result})
    totals = {}
    for name in results[0]["fixed_constructions"]:
        scores = [case["fixed_constructions"][name] for case in results]
        totals[name] = {"exact": sum(row["exact"] for row in scores),
                        "samples": sum(row["samples"] for row in scores),
                        "max_channel_delta": [max(row["max_channel_delta"][k] for row in scores) for k in range(4)]}
    return {"source_readback_pixels_exact": 22080, "native_matrix_readbacks": matrices,
            "cases": results, "totals": totals,
            "centroid_interval_assumption": "Conditional final floor(step*weighted_source_index); not an admitted operation order",
            "selection": "Every fixed construction is evaluated at every geometry-selected interior; no RGB-selected route",
            "native_api": "Drawing API beginBitmapFill(false, true), not a preserved DefineShape fill65 tag",
            "source_tag_equivalence_proved": False,
            "sampler_admitted": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(result["totals"])
