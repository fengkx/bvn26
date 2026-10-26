"""Constrain common impulse weights without selecting coefficients from readbacks."""
import argparse
from collections import defaultdict
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_affine_initializers import sample_fixed
from tools.probes.analyze_jinye_deep_gradients import deep_points
from tools.probes.analyze_jinye_translation_controls import actual_spec, models_for
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_red_impulses import decode, source_pixel
from tools.probes.decode_jinye_tag_controls import decode as decode_old

AMPLITUDES = (64, 128, 255)


def weight_interval(values, denominator):
    if len(values) != 3 or denominator <= 0:
        raise ValueError("Incomplete amplitude constraints")
    if any(not isinstance(value, int) or not 0 <= value <= amplitude for value, amplitude in zip(values, AMPLITUDES)):
        raise ValueError("Impulse output outside authored amplitude")
    lower = max((value*denominator+amplitude-1)//amplitude for value, amplitude in zip(values, AMPLITUDES))
    upper = min(((value+1)*denominator+amplitude-1)//amplitude-1 for value, amplitude in zip(values, AMPLITUDES))
    return max(0, lower), min(denominator, upper)


def real_weight_interval(values):
    weight_interval(values, 256)
    return max(Fraction(value, amplitude) for value, amplitude in zip(values, AMPLITUDES)), min(Fraction(value+1, amplitude) for value, amplitude in zip(values, AMPLITUDES))


def real_counterexamples(cases):
    failures = []
    for case in cases:
        for row in case["constraints"]:
            lower, upper = real_weight_interval(row[2:5])
            if lower >= upper:
                failures.append({key: case[key] for key in ("base_case", "shape", "scale", "corner", "cached")}
                                | {"x": row[0], "y": row[1], "native_red_64_128_255": row[2:5],
                                   "lower_inclusive": str(lower), "upper_exclusive": str(upper)})
    return failures


def verify_gray_reference(fixture, captures, matrices, old_fixture, old_captures, old_matrices):
    results = []
    for capture in captures:
        spec = fixture["cases"][capture["source_case"]]
        if spec["amplitude"] != 255:
            continue
        base = old_fixture["cases"][spec["base_case"]]
        for key in ("shape", "matrix", "outer", "draw", "fill", "mask"):
            assert spec[key] == base[key]
        assert matrices[spec["id"]][1:19] == old_matrices[base["id"]][1:19]
        previous = old_captures[base["id"]*2+int(capture["cached"])]
        assert previous["source_case"] == base["id"] and previous["cached"] == capture["cached"]
        failures = [[i % 96, i//96, a[0], b[0], a[3], b[3]]
                    for i, (a, b) in enumerate(zip(capture["pixels"], previous["pixels"]))
                    if (a[0], a[3]) != (b[0], b[3])]
        assert len(capture["pixels"]) == len(previous["pixels"]) == 96*96
        results.append({"case": spec["id"], "base_case": base["id"], "cached": capture["cached"],
                        "samples": 96*96, "red_alpha_exact": 96*96-len(failures), "failures": failures})
    return results


def analyze(native):
    fixture, sources, captures, matrices = decode(native)
    generated = [[source_pixel(source, x, y) for y in range(40) for x in range(92)] for source in range(12)]
    assert sources == generated
    old_fixture, _, old_captures, old_matrices = decode_old(ROOT/"evidence/importer-loud-fail/r223/native")
    gray = verify_gray_reference(fixture, captures, matrices, old_fixture, old_captures, old_matrices)
    grouped = defaultdict(dict)
    for capture in captures:
        spec = fixture["cases"][capture["source_case"]]
        key = spec["base_case"], capture["cached"]
        assert spec["amplitude"] not in grouped[key]
        grouped[key][spec["amplitude"]] = capture
    results = []
    for (base, cached), members in grouped.items():
        assert set(members) == set(AMPLITUDES)
        specifications = [fixture["cases"][members[a]["source_case"]] for a in AMPLITUDES]
        spec = actual_spec(specifications[0], matrices[specifications[0]["id"]])
        for other in specifications[1:]:
            assert all(other[key] == specifications[0][key] for key in ("matrix", "outer", "draw", "fill", "mask", "shape", "corner"))
        shape = next(row for row in fixture["source_graph"]["shapes"] if row["id"] == spec["shape"])
        models, _, polygon = models_for(spec, shape)
        points = deep_points(tuple(polygon), (96, 96), 2)
        constraints = []
        invariants = []
        for x, y in points:
            values = [members[a]["pixels"][y*96+x] for a in AMPLITUDES]
            for amplitude, pixel in zip(AMPLITUDES, values):
                if pixel[1:] != [0, 73, 255]:
                    invariants.append([x, y, amplitude, pixel])
            red = [pixel[0] for pixel in values]
            intervals = [weight_interval(red, denominator) for denominator in (256, 65536)]
            constraints.append([x, y, *red, *intervals[0], *intervals[1]])
        scores = {}
        for model, fixed in models.items():
            for order in ("byte_weights", "vertical_horizontal"):
                exact = active = active_exact = 0
                by_amplitude = [0]*3
                maxima = [0]*3
                failures = []
                for row in constraints:
                    x, y = row[:2]
                    expected = row[2:5]
                    actual = [sample_fixed(generated[entry["source"]], fixed, x, y, order)[0] for entry in specifications]
                    equal = actual == expected
                    exact += equal
                    support = any(expected) or any(actual)
                    active += support
                    active_exact += support and equal
                    for index, (a, b) in enumerate(zip(actual, expected)):
                        by_amplitude[index] += a == b
                        maxima[index] = max(maxima[index], abs(a-b))
                    if not equal:
                        failures.append([x, y, *actual, *expected])
                scores[model+"/"+order] = {"coordinate_triples": len(points), "triples_exact": exact,
                                          "active_union": active, "active_union_exact": active_exact,
                                          "amplitudes_exact": by_amplitude, "max_red_delta": maxima,
                                          "failures": failures}
        active_constraints = [row for row in constraints if any(row[2:5])]
        results.append({"base_case": base, "shape": spec["shape"], "scale": spec["draw"][0],
                        "corner": spec["corner"], "cached": cached, "deep_samples": len(points),
                        "observed_nonzero_union": len(active_constraints),
                        "constraints": constraints, "invariant_failures": invariants,
                        "weight256_infeasible": sum(row[5] > row[6] for row in constraints),
                        "weight65536_infeasible": sum(row[7] > row[8] for row in constraints),
                        "active_weight256_infeasible": sum(row[5] > row[6] for row in active_constraints),
                        "active_weight65536_infeasible": sum(row[7] > row[8] for row in active_constraints),
                        "models": scores})
    totals = {}
    for model in results[0]["models"]:
        rows = [case["models"][model] for case in results]
        totals[model] = {"coordinate_triples": sum(row["coordinate_triples"] for row in rows),
                         "triples_exact": sum(row["triples_exact"] for row in rows),
                         "active_union": sum(row["active_union"] for row in rows),
                         "active_union_exact": sum(row["active_union_exact"] for row in rows),
                         "max_red_delta": [max(row["max_red_delta"][i] for row in rows) for i in range(3)]}
    prior_path = ROOT/"evidence/importer-loud-fail/r225/analysis.json.gz"
    prior = json.loads(gzip.decompress(prior_path.read_bytes()))
    real_failures = real_counterexamples(results)
    return {"source_pixels_exact": 44160, "gray255_comparisons": gray,
            "gray255_red_alpha_exact": sum(row["red_alpha_exact"] for row in gray),
            "gray255_pixels": sum(row["samples"] for row in gray),
            "cases": results, "totals": totals,
            "deep_coordinate_triples": sum(row["deep_samples"] for row in results),
            "observed_nonzero_union": sum(row["observed_nonzero_union"] for row in results),
            "invariant_failure_count": sum(len(row["invariant_failures"]) for row in results),
            "weight256_infeasible": sum(row["weight256_infeasible"] for row in results),
            "weight65536_infeasible": sum(row["weight65536_infeasible"] for row in results),
            "real_single_floor_weight_infeasible": len(real_failures),
            "real_single_floor_counterexamples": real_failures,
            "weight_constraints": "floor(amplitude*weight/denominator); intervals reject only, no coefficient selected",
            "retained_full_r225_totals": prior["totals"],
            "retained_r225_sha256": hashlib.sha256(prior_path.read_bytes()).hexdigest(),
            "geometry_selection_uses_native_pixels": False, "admission_suite_reduced": False,
            "coefficient_selected_from_interval": False, "candidate_admitted": False,
            "gpu_advance_allowed": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    print(json.dumps({key: value for key, value in result.items() if key not in ("cases", "gray255_comparisons", "retained_full_r225_totals")}, indent=2))
