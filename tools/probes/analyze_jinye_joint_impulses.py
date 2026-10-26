"""Reject bounded separable interpolation families without choosing render coordinates."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.build_bound_bitmap_component import ROOT

AMPLITUDES = (64, 128, 255)
CORNERS = ((45, 19), (46, 19), (45, 20), (46, 20))
# Every contiguous 2x2 cell touching a known impulse; all other cells are disjoint.
CELLS = tuple((x, y) for y in range(18, 21) for x in range(44, 47))
ORDERS = ("vertical_horizontal", "horizontal_vertical")


def staged(amplitude, wx, wy, order):
    if order == "vertical_horizontal":
        return ((amplitude * wy) // 256 * wx) // 256
    if order == "horizontal_vertical":
        return ((amplitude * wx) // 256 * wy) // 256
    raise ValueError("Unknown global interpolation order")


def response(cell, fx, fy, order):
    if not 0 <= fx < 256 or not 0 <= fy < 256 or cell not in CELLS:
        raise ValueError("Outside declared contiguous bilinear family")
    result = []
    for x, y in CORNERS:
        dx, dy = x-cell[0], y-cell[1]
        wx = (256-fx, fx)[dx] if dx in (0, 1) else 0
        wy = (256-fy, fy)[dy] if dy in (0, 1) else 0
        result.extend(staged(a, wx, wy, order) for a in AMPLITUDES)
    return tuple(result)


def feasible_signatures(wanted):
    """Exhaustively count existence, never return a satisfying cell or fraction."""
    counts = {order: Counter() for order in ORDERS}
    for order in ORDERS:
        if (0,)*12 in wanted:
            counts[order][(0,)*12] += 1  # Explicit disjoint-footprint state.
        for cell in CELLS:
            for fy in range(256):
                for fx in range(256):
                    values = response(cell, fx, fy, order)
                    if values in wanted:
                        counts[order][values] += 1
    return counts


def joint_groups(prior):
    grouped = defaultdict(dict)
    for case in prior["cases"]:
        key = case["shape"], case["scale"], case["cached"]
        assert case["corner"] not in grouped[key]
        grouped[key][case["corner"]] = case
    result = []
    for (shape, scale, cached), corners in grouped.items():
        assert set(corners) == set(range(4))
        points = [tuple(row[:2]) for row in corners[0]["constraints"]]
        assert all([tuple(row[:2]) for row in c["constraints"]] == points for c in corners.values())
        rows = []
        for i, (x, y) in enumerate(points):
            values = tuple(v for corner in range(4) for v in corners[corner]["constraints"][i][2:5])
            rows.append((x, y, values))
        result.append({"shape": shape, "scale": scale, "cached": cached,
                       "base_cases_by_corner": [corners[c]["base_case"] for c in range(4)], "rows": rows})
    return result


def analyze(path):
    raw = path.read_bytes()
    prior = json.loads(gzip.decompress(raw))
    assert prior["source_pixels_exact"] == 44160
    assert prior["gray255_red_alpha_exact"] == prior["gray255_pixels"] == 294912
    assert prior["invariant_failure_count"] == 0
    groups = joint_groups(prior)
    wanted = {values for group in groups for _, _, values in group["rows"]}
    counts = feasible_signatures(wanted)
    results = []
    for group in groups:
        rows = group.pop("rows")
        active = sum(any(v) for _, _, v in rows)
        sums = Counter(tuple(sum(v[c*3+a] for c in range(4)) for a in range(3)) for _, _, v in rows)
        orders = {}
        for order in ORDERS:
            failures = [[x, y, list(v)] for x, y, v in rows if counts[order][v] == 0]
            orders[order] = {"feasible": len(rows)-len(failures), "infeasible": len(failures),
                             "active_feasible": active-sum(any(row[2]) for row in failures), "failures": failures}
        results.append(group | {"coordinates": len(rows), "observed_active_union": active,
                               "sum_responses_64_128_255": [[*s, n] for s, n in sorted(sums.items())], "orders": orders})
    totals = {order: {key: sum(row["orders"][order][key] for row in results)
                      for key in ("feasible", "infeasible", "active_feasible")} for order in ORDERS}
    return {"cases": results, "totals": totals, "coordinates": sum(c["coordinates"] for c in results),
            "observed_active_union": sum(c["observed_active_union"] for c in results),
            "unique_native_signatures": len(wanted),
            "family": {"cells": CELLS, "disjoint_state": True, "fractions": "integers 0..255 / 256", "orders": ORDERS,
                       "scope": "one common contiguous 2x2 footprint and fractions for all four corners and three amplitudes"},
            "retained_r227_sha256": hashlib.sha256(raw).hexdigest(),
            "retained_r227_totals": prior["totals"], "retained_r225_sha256": prior["retained_r225_sha256"],
            "retained_r227_real_weight_counterexamples": prior["real_single_floor_counterexamples"],
            "geometry_selection_uses_native_pixels": False, "admission_suite_reduced": False,
            "existential_constraints_only": True, "selected_render_coordinates": False,
            "initializer_proved": False, "candidate_admitted": False, "gpu_advance_allowed": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior", type=Path, default=ROOT/"evidence/importer-loud-fail/r227/analysis.json.gz")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.prior)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("cases", "retained_r227_totals", "retained_r227_real_weight_counterexamples")}, indent=2))
