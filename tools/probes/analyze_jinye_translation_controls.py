"""Measure independently read-back translation consumption with global models."""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path

from tools.probes.analyze_jinye_affine_initializers import fixed_rows, hypotheses, sample_fixed
from tools.probes.analyze_jinye_smooth_controls import interior_geometry
from tools.probes.analyze_jinye_smooth_leaf import compose, source_geometry
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_affine_controls import source_pixel
from tools.probes.decode_jinye_translation_controls import decode


def actual_spec(requested, readback):
    assert int(readback[0]) == requested["id"] and len(readback) == 23
    actual = dict(requested)
    actual["matrix"] = list(requested["matrix"])
    # The decoder independently checks that these readbacks lie on the twip grid.
    # Recover their exact twip values rather than reusing the requested offsets.
    for axis in range(2):
        observed = Fraction(str(readback[5+axis]))
        assert (observed*20).denominator == 1
        actual["matrix"][4+axis] = observed
    return actual


def models_for(spec, shape):
    models, direct, polygon = hypotheses(spec, shape)
    child = compose(list(map(Fraction, spec["outer"])), list(map(Fraction, spec["matrix"])))
    draw = list(map(Fraction, spec["draw"]))
    linear_draw = draw[:4]+[Fraction(0), Fraction(0)]
    transformed = compose(linear_draw, child)
    transformed[4:] = [Fraction(round(value*4), 4)+Fraction(math.trunc(offset*4), 4)
                       for value, offset in zip(transformed[4:], draw[4:])]
    consumed = dict(spec, matrix=transformed, outer=[1, 0, 0, 1, 0, 0], draw=[1, 0, 0, 1, 0, 0])
    matrix, _ = source_geometry(consumed, shape)
    for footprint in ("center", "minimum"):
        models["scaled_child_then_draw_quarters/"+footprint] = fixed_rows(matrix, footprint)
    return models, direct, polygon


def compare(source, spec, shape, target):
    models, direct, polygon = models_for(spec, shape)
    geometry, points = interior_geometry(tuple(direct), tuple(polygon), (48, 48))
    scores = {}
    for model, rows in models.items():
        for order in ("byte_weights", "vertical_horizontal"):
            exact = active = active_exact = 0
            differences = [Counter() for _ in range(4)]
            failures = []
            for x, y, _ in points:
                actual = sample_fixed(source, rows, x, y, order)
                native = target[y*48+x]
                equal = actual == native
                exact += equal
                support = any(actual[:3]) or any(native[:3])
                active += support
                active_exact += support and equal
                for histogram, a, b in zip(differences, actual, native):
                    histogram[a-b] += 1
                if not equal:
                    failures.append([x, y, actual, native])
            scores[model+"/"+order] = {
                "samples": len(points), "exact": exact,
                "nonzero_rgb_union": active, "nonzero_rgb_union_exact": active_exact,
                "max_channel_delta": [max(map(abs, h), default=0) for h in differences],
                "signed_rgba_delta_histograms": [dict(sorted(h.items())) for h in differences],
                "failures": failures,
            }
    return {"geometry_classes": geometry, "models": scores}


def native_pair_comparisons(fixture, captures, readbacks):
    specifications = fixture["cases"]
    assert len(specifications) % 9 == 0
    indexed = {(row["source_case"], row["cached"]): row for row in captures}
    assert len(indexed) == len(captures) == len(specifications)*2
    pairs = []
    for start in range(0, len(specifications), 9):
        group = specifications[start:start+9]
        assert [row["offset"] for row in group] == [-1/64, 0, 1/64, 7/64, 8/64, 9/64, 15/64, 16/64, 17/64]
        for key in ("base_case", "operand", "axis", "source", "shape", "quarter_origin"):
            assert all(row[key] == group[0][key] for row in group)
        for cached in (False, True):
            for left, right in zip(group, group[1:]):
                a = indexed[left["id"], cached]["pixels"]
                b = indexed[right["id"], cached]["pixels"]
                assert len(a) == len(b) == fixture["size"][0]*fixture["size"][1]
                pairs.append({"cases": [left["id"], right["id"]], "cached": cached,
                              "operand": left["operand"], "axis": left["axis"],
                              "source": left["source"], "shape": left["shape"], "scale": left["draw"][0],
                              "offsets": [left["offset"], right["offset"]],
                              "changed_pixels": sum(p != q for p, q in zip(a, b)),
                              "max_delta": max((abs(v-w) for p, q in zip(a, b) for v, w in zip(p, q)), default=0),
                              "child_translation_equal": readbacks[left["id"]][5:7] == readbacks[right["id"]][5:7],
                              "draw_translation_equal": readbacks[left["id"]][17:19] == readbacks[right["id"]][17:19]})
    return pairs


def analyze(native):
    fixture, sources, captures, readbacks = decode(native)
    generated = [[source_pixel(index, x, y) for y in range(40) for x in range(92)] for index in range(2)]
    assert generated == sources
    properties = []
    rows = []
    for capture in captures:
        requested = fixture["cases"][capture["source_case"]]
        actual = actual_spec(requested, readbacks[requested["id"]])
        if not capture["cached"]:
            properties.append({"case": requested["id"], "operand": requested["operand"],
                               "axis": requested["axis"], "offset": requested["offset"],
                               "requested_child_translation": requested["matrix"][4:],
                               "actual_child_translation": list(map(str, actual["matrix"][4:])),
                               "actual_draw_translation": readbacks[requested["id"]][17:19],
                               "child_changed": any(Fraction(str(a)) != b for a, b in zip(requested["matrix"][4:], actual["matrix"][4:]))})
        shape = next(s for s in fixture["source_graph"]["shapes"] if s["id"] == actual["shape"])
        rows.append({"case": actual["id"], "source": actual["source"], "shape": actual["shape"],
                     "scale": actual["draw"][0], "operand": actual["operand"], "axis": actual["axis"],
                     "offset": actual["offset"], "cached": capture["cached"], "native_bounds": capture["bounds"],
                     **compare(generated[actual["source"]], actual, shape, capture["pixels"])})
    totals = {}
    for model in rows[0]["models"]:
        scores = [row["models"][model] for row in rows]
        totals[model] = {"exact": sum(score["exact"] for score in scores),
                         "samples": sum(score["samples"] for score in scores),
                         "max_channel_delta": [max(score["max_channel_delta"][k] for score in scores) for k in range(4)]}
    prior_path = ROOT/"evidence/importer-loud-fail/r224/analysis.json.gz"
    prior = json.loads(gzip.decompress(prior_path.read_bytes()))
    return {"source_pixels_exact": 7360, "matrix_readbacks": readbacks,
            "native_adjacent_pairs": native_pair_comparisons(fixture, captures, readbacks),
            "property_consumption": properties, "cases": rows, "totals": totals,
            "r224_retained_rejection_totals": prior["totals"],
            "r224_analysis_sha256": hashlib.sha256(prior_path.read_bytes()).hexdigest(),
            "cache_bounds_used_as_allocation_origins": False,
            "scaled_child_translation_transfer_hypothesis_tested": True,
            "compound_affine_translation_rule_proved": False,
            "candidate_admitted": False, "gpu_advance_allowed": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    print(json.dumps(result["totals"], indent=2))
