"""Isolate fixed-model ramp gradients without reducing any admission suite."""
import argparse
from collections import Counter
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_affine_initializers import sample_fixed
from tools.probes.analyze_jinye_smooth_leaf import inside
from tools.probes.analyze_jinye_translation_controls import actual_spec, models_for
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_affine_controls import source_pixel
from tools.probes.decode_jinye_translation_controls import decode


@lru_cache(maxsize=288)
def deep_points(polygon, size, margin=2):
    if margin < 0:
        raise ValueError("Negative geometry margin")
    return tuple((x, y) for y in range(size[1]) for x in range(size[0])
                 if all(inside(point, polygon) for point in
                        ((x-margin, y-margin), (x+1+margin, y-margin),
                         (x+1+margin, y+1+margin), (x-margin, y+1+margin))))


def level_and_gradient_score(predicted, native, points):
    point_set = set(points)
    levels = Counter(predicted[point]-native[point] for point in points)
    failures = [[x, y, predicted[x, y], native[x, y]] for x, y in points if predicted[x, y] != native[x, y]]
    gradients = {}
    for axis, step in (("horizontal", (1, 0)), ("vertical", (0, 1))):
        pairs = [(point, (point[0]+step[0], point[1]+step[1])) for point in points
                 if (point[0]+step[0], point[1]+step[1]) in point_set]
        deltas = Counter()
        residuals = []
        for first, second in pairs:
            actual = predicted[second]-predicted[first]
            expected = native[second]-native[first]
            deltas[actual-expected] += 1
            if actual != expected:
                residuals.append([*first, actual, expected])
        gradients[axis] = {"samples": len(pairs), "exact": deltas[0],
                           "delta_histogram": dict(sorted(deltas.items())), "failures": residuals}
    return {"samples": len(points), "levels_exact": levels[0],
            "level_residual_histogram": dict(sorted(levels.items())),
            "level_failures": failures, "gradients": gradients}


def compare(source, spec, shape, target, size=(48, 48)):
    assert len(target) == size[0]*size[1]
    models, _, polygon = models_for(spec, shape)
    points = deep_points(tuple(polygon), tuple(size), 2)
    channel = spec["source"]
    assert channel in (0, 1)
    native = {(x, y): target[y*size[0]+x][channel] for x, y in points}
    invariant_failures = [[x, y, target[y*size[0]+x]] for x, y in points
                          if target[y*size[0]+x][2:] != [73, 255] or target[y*size[0]+x][1-channel] != 0]
    scores = {}
    for model, rows in models.items():
        for order in ("byte_weights", "vertical_horizontal"):
            predicted = {(x, y): sample_fixed(source, rows, x, y, order)[channel] for x, y in points}
            scores[model+"/"+order] = level_and_gradient_score(predicted, native, points)
    return {"deep_geometry_samples": len(points), "invariant_failures": invariant_failures,
            "opaque_constant_channel_invariants_exact": not invariant_failures,
            "models": scores}


def image_buckets(pairs, captures):
    parents = {(capture["source_case"], capture["cached"]): (capture["source_case"], capture["cached"]) for capture in captures}
    def root(key):
        while parents[key] != key:
            key = parents[key]
        return key
    for pair in pairs:
        if pair["changed_pixels"] == 0:
            left, right = [(case, pair["cached"]) for case in pair["cases"]]
            left, right = root(left), root(right)
            parents[max(left, right)] = min(left, right)
    return {key: root(key)[0] for key in parents}


def analyze(native, prior_path):
    raw = prior_path.read_bytes()
    prior = json.loads(gzip.decompress(raw) if prior_path.suffix == ".gz" else raw)
    prior_totals, pairs = prior["totals"], prior["native_adjacent_pairs"]
    prior_matrices = prior["matrix_readbacks"]
    prior_identity = [(row["case"], row["cached"], row["shape"], row["source"], row["scale"],
                       row["operand"], row["axis"], row["offset"], row["native_bounds"]) for row in prior["cases"]]
    assert not prior["candidate_admitted"] and not prior["production_admitted"]
    del prior
    fixture, sources, captures, matrices = decode(native)
    assert prior_matrices == matrices
    identity = []
    for capture in captures:
        spec = fixture["cases"][capture["source_case"]]
        identity.append((spec["id"], capture["cached"], spec["shape"], spec["source"], spec["draw"][0],
                         spec["operand"], spec["axis"], spec["offset"], capture["bounds"]))
    assert prior_identity == identity
    buckets = image_buckets(pairs, captures)
    generated = [[source_pixel(index, x, y) for y in range(40) for x in range(92)] for index in range(2)]
    assert sources == generated
    cases = []
    for capture in captures:
        requested = fixture["cases"][capture["source_case"]]
        spec = actual_spec(requested, matrices[requested["id"]])
        shape = next(row for row in fixture["source_graph"]["shapes"] if row["id"] == spec["shape"])
        cases.append({"case": spec["id"], "shape": spec["shape"], "source": spec["source"],
                      "scale": spec["draw"][0], "cached": capture["cached"],
                      "operand": spec["operand"], "axis": spec["axis"], "offset": spec["offset"],
                      "native_unchanged_image_bucket": buckets[spec["id"], capture["cached"]],
                      **compare(generated[spec["source"]], spec, shape, capture["pixels"])})
    totals = {}
    for model in cases[0]["models"]:
        rows = [case["models"][model] for case in cases]
        totals[model] = {"samples": sum(row["samples"] for row in rows),
                         "levels_exact": sum(row["levels_exact"] for row in rows),
                         "gradients": {axis: {"samples": sum(row["gradients"][axis]["samples"] for row in rows),
                                                "exact": sum(row["gradients"][axis]["exact"] for row in rows)}
                                       for axis in ("horizontal", "vertical")}}
    return {"prior_analysis_sha256": hashlib.sha256(raw).hexdigest(),
            "retained_full_suite_rejections": prior_totals,
            "geometry_margin_pixels": 2, "geometry_selection_uses_native_pixels": False,
            "image_bucket_is_measurement_annotation_only": True,
            "admission_suite_reduced": False, "cases": cases, "totals": totals,
            "deep_geometry_samples": sum(case["deep_geometry_samples"] for case in cases),
            "invariant_failure_count": sum(len(case["invariant_failures"]) for case in cases),
            "candidate_admitted": False, "gpu_advance_allowed": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=ROOT/"evidence/importer-loud-fail/r225/native")
    parser.add_argument("--prior-analysis", type=Path, default=ROOT/"evidence/importer-loud-fail/r225/analysis.json.gz")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native, args.prior_analysis)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    print(json.dumps({key: result[key] for key in ("deep_geometry_samples", "invariant_failure_count", "totals")}, indent=2))
