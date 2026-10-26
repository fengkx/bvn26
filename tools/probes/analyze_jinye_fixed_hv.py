"""Test globally fixed horizontal-then-vertical arithmetic with independent coordinates."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_affine_initializers import decode_jpeg, decode_leaves
from tools.probes.analyze_jinye_smooth_controls import interior_geometry
from tools.probes.analyze_jinye_translation_controls import actual_spec, models_for
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_affine_controls import source_pixel
from tools.probes.decode_jinye_tag_controls import decode as decode_tags
from tools.probes.decode_jinye_translation_controls import decode as decode_translations
from tools.probes.decode_jinye_red_impulses import decode as decode_impulses, source_pixel as red_source


def interpolate_hv(pixels, fx, fy):
    top = [(pixels[0][k]*(256-fx)+pixels[1][k]*fx)//256 for k in range(4)]
    bottom = [(pixels[2][k]*(256-fx)+pixels[3][k]*fx)//256 for k in range(4)]
    return [(top[k]*(256-fy)+bottom[k]*fy)//256 for k in range(4)]


def sample_hv(source, rows, x, y):
    sx, sy = [a*x+b*y+t+offset-32768 for a, b, t, offset in rows]
    ix, iy = sx//65536, sy//65536
    fx, fy = (sx % 65536)//256, (sy % 65536)//256
    pixels = [source[max(0, min(39, iy+dy))*92+max(0, min(91, ix+dx))]
              for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
    return interpolate_hv(pixels, fx, fy)


def compare(source, spec, shape, target, size):
    assert len(source) == 3680 and len(target) == size[0]*size[1]
    models, direct, polygon = models_for(spec, shape)
    geometry, points = interior_geometry(tuple(direct), tuple(polygon), tuple(size))
    scores = {}
    for model, rows in models.items():
        failures = []
        histograms = [Counter() for _ in range(4)]
        active = active_exact = red_active = red_exact = 0
        for x, y, _ in points:
            actual = sample_hv(source, rows, x, y)
            native = target[y*size[0]+x]
            support = any(actual[:3]) or any(native[:3])
            active += support
            active_exact += support and actual == native
            red_support = bool(actual[0] or native[0])
            red_active += red_support
            red_exact += red_support and actual == native
            for histogram, a, b in zip(histograms, actual, native):
                histogram[a-b] += 1
            if actual != native:
                failures.append([x, y, actual, native])
        scores[model] = {"samples": len(points), "exact": len(points)-len(failures),
                         "nonzero_rgb_union": active, "nonzero_rgb_union_exact": active_exact,
                         "nonzero_red_union": red_active, "nonzero_red_union_exact": red_exact,
                         "max_channel_delta": [max(map(abs, h), default=0) for h in histograms],
                         "signed_rgba_delta_histograms": [dict(sorted(h.items())) for h in histograms],
                         "fixed_rows": rows, "failures": failures}
    return {"geometry_classes": geometry, "models": scores}


def run_controls(round_number, decoder, generator, size):
    fixture, sources, captures, matrices = decoder(ROOT/f"evidence/importer-loud-fail/r{round_number}/native")
    assert sources == [[generator(i, x, y) for y in range(40) for x in range(92)] for i in range(len(sources))]
    results = []
    for capture in captures:
        requested = fixture["cases"][capture["source_case"]]
        spec = actual_spec(requested, matrices[requested["id"]]) if round_number == 225 else requested
        shape = next(s for s in fixture["source_graph"]["shapes"] if s["id"] == spec["shape"])
        results.append({"case": spec["id"], "shape": spec["shape"], "source": spec["source"],
                        "scale": spec["draw"][0], "cached": capture["cached"],
                        **compare(sources[spec["source"]], spec, shape, capture["pixels"], size)})
    return results


def analyze(dump, output):
    results = {"r223_controls": run_controls(223, decode_tags, source_pixel, (96, 96)),
               "r225_translation": run_controls(225, decode_translations, source_pixel, (48, 48)),
               "r227_red_impulses": run_controls(227, decode_impulses, red_source, (96, 96))}
    fixture, captures, _ = decode_leaves(ROOT/"evidence/importer-loud-fail/r221/native")
    decoder, pixels = decode_jpeg(dump, output/"decoded")
    leaves = []
    for capture in captures:
        spec = fixture["cases"][capture["source_case"]]
        shape = next(s for s in fixture["shapes"] if s["id"] == spec["shape"])
        leaves.append({"case": spec["id"], "shape": spec["shape"], "cached": capture["cached"],
                       **compare(pixels, spec, shape, capture["pixels"], (600, 400))})
    results["r221_jpeg"] = leaves
    totals = {}
    for family, cases in results.items():
        totals[family] = {}
        for model in cases[0]["models"]:
            scores = [case["models"][model] for case in cases]
            totals[family][model] = {key: sum(row[key] for row in scores)
                                     for key in ("samples", "exact", "nonzero_rgb_union", "nonzero_rgb_union_exact", "nonzero_red_union", "nonzero_red_union_exact")}
            totals[family][model]["max_channel_delta"] = [max(row["max_channel_delta"][k] for row in scores) for k in range(4)]
    retained = {}
    for r in (224, 225, 227):
        path = ROOT/f"evidence/importer-loud-fail/r{r}/analysis.json.gz"
        raw = path.read_bytes()
        old = json.loads(gzip.decompress(raw))
        retained[str(r)] = {"sha256": hashlib.sha256(raw).hexdigest(), "totals": old["totals"]}
    return {"cases": results, "totals": totals, "retained": retained, "decoder": decoder,
            "interpolation_order": "horizontal_vertical", "feasibility_coefficients_used": False,
            "coordinate_models_unchanged": True, "affine_applicability_proved": False,
            "axis_repeat_implementation_changed": False, "global_axis_applicability_claimed": False,
            "geometry_selection_uses_native_pixels": False, "admission_suite_reduced": False,
            "candidate_admitted": False, "gpu_advance_allowed": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = analyze(args.dump, args.output)
    (args.output/"analysis.json").write_text(json.dumps(result, separators=(",", ":"))+"\n")
    print(json.dumps(result["totals"], indent=2))
