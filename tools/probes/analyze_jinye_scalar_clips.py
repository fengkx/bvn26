"""Compare fixed HV models at matched scalar-clip and full-image coordinates."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_fixed_hv import sample_hv
from tools.probes.analyze_jinye_smooth_controls import interior_geometry
from tools.probes.analyze_jinye_translation_controls import models_for
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_clip_controls import decode


def matched_points(points, clip):
    x, y, width, height = clip
    if width != 1:
        raise ValueError("Scalar diagnostic requires width one")
    return [(px, py) for px, py, _ in points if x <= px < x+width and y <= py < y+height]


def score(source, rows, points, scalar, full, size):
    if len(scalar) != len(full) or len(full) != size[0]*size[1]:
        raise ValueError("Image extent mismatch")
    histograms = {kind: [Counter() for _ in range(4)] for kind in ("scalar", "full", "native_pair")}
    exact = Counter()
    transitions = Counter()
    failures = []
    active = active_scalar_exact = active_full_exact = 0
    for x, y in points:
        actual = sample_hv(source, rows, x, y)
        a, b = scalar[y*size[0]+x], full[y*size[0]+x]
        scalar_exact, full_exact = actual == a, actual == b
        support = any(actual[:3]) or any(a[:3]) or any(b[:3])
        active += support
        active_scalar_exact += support and scalar_exact
        active_full_exact += support and full_exact
        exact["scalar"] += scalar_exact
        exact["full"] += full_exact
        exact["native_pair"] += a == b
        transitions[f"full_{'exact' if full_exact else 'fails'}_scalar_{'exact' if scalar_exact else 'fails'}"] += 1
        for name, left, right in (("scalar", actual, a), ("full", actual, b), ("native_pair", a, b)):
            for histogram, lv, rv in zip(histograms[name], left, right):
                histogram[lv-rv] += 1
        if actual != a or actual != b:
            failures.append([x, y, actual, a, b])
    return {"samples": len(points), "exact": dict(exact), "transitions": dict(transitions),
            "nonzero_rgb_union": active, "nonzero_rgb_union_scalar_exact": active_scalar_exact,
            "nonzero_rgb_union_full_exact": active_full_exact,
            "max_channel_delta": {key: [max(map(abs, h), default=0) for h in hs] for key, hs in histograms.items()},
            "signed_rgba_delta_histograms": {key: [dict(sorted(h.items())) for h in hs] for key, hs in histograms.items()},
            "failures": failures}


def analyze(native):
    fixture, sources, captures, _ = decode(native)
    size = tuple(fixture["size"])
    by_key = {(c["source_case"], c["cached"], c["clip_id"]): c for c in captures}
    assert len(by_key) == len(captures)
    baseline = fixture["clips"].index(None)
    results = []
    for spec in fixture["cases"]:
        shape = next(s for s in fixture["source_graph"]["shapes"] if s["id"] == spec["shape"])
        models, direct, polygon = models_for(spec, shape)
        _, interior = interior_geometry(tuple(direct), tuple(polygon), size)
        for cached in (False, True):
            full = by_key[spec["id"], cached, baseline]
            for clip_id, clip in enumerate(fixture["clips"]):
                if clip is None or clip[2] != 1:
                    continue
                points = matched_points(interior, clip)
                scalar = by_key[spec["id"], cached, clip_id]
                assert scalar["bounds"] == full["bounds"]
                scores = {name: score(sources[spec["source"]], rows, points, scalar["pixels"], full["pixels"], size)
                          for name, rows in models.items()}
                results.append({"case": spec["id"], "shape": spec["shape"], "source": spec["source"],
                                "scale": spec["draw"][0], "cached": cached, "clip_id": clip_id, "clip": clip,
                                "geometry_points": points, "models": scores})
    totals = {}
    for model in results[0]["models"]:
        scores = [r["models"][model] for r in results]
        transitions = Counter()
        for s in scores:
            transitions.update(s["transitions"])
        totals[model] = {"samples": sum(s["samples"] for s in scores),
                         "exact": {key: sum(s["exact"].get(key, 0) for s in scores) for key in ("scalar", "full", "native_pair")},
                         "transitions": dict(transitions),
                         "max_channel_delta": {key: [max(s["max_channel_delta"][key][k] for s in scores) for k in range(4)]
                                               for key in ("scalar", "full", "native_pair")}}
    retained = {str(r): hashlib.sha256((ROOT/f"evidence/importer-loud-fail/r{r}/analysis.json.gz").read_bytes()).hexdigest()
                for r in (229, 230)}
    return {"cases": results, "totals": totals, "retained_analysis_sha256": retained,
            "native_fixture_sha256": hashlib.sha256((native/"fixture.json").read_bytes()).hexdigest(),
            "matched_membership": "same authored full-pixel geometry interior intersected with declared width-one clip",
            "geometry_selection_uses_native_pixels": False, "offset_fitted": False,
            "coordinate_models_unchanged": True, "admission_suite_reduced": False,
            "candidate_admitted": False, "gpu_advance_allowed": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=ROOT/"evidence/importer-loud-fail/r230/native")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    print(json.dumps(result["totals"], indent=2))
