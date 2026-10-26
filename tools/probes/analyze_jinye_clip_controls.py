"""Compare fixed-coordinate native pixels when only destination clips change."""
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path

from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_tag_controls import decode as decode_old


def clip_points(rect, size):
    if len(rect) != 4 or any(type(v) is not int for v in rect):
        raise ValueError("Clip rectangle must contain four integer values")
    x, y, width, height = rect
    if width < 0 or height < 0:
        raise ValueError("Negative clip extent")
    return {(px, py) for py in range(max(0, y), min(size[1], y+height))
            for px in range(max(0, x), min(size[0], x+width))}


def compare_at(left, right, points, size):
    if len(left) != size[0]*size[1] or len(right) != len(left):
        raise ValueError("Native image extent changed")
    failures = []
    histograms = [Counter() for _ in range(4)]
    active = active_exact = red_active = red_exact = 0
    for x, y in sorted(points, key=lambda p: (p[1], p[0])):
        a, b = left[y*size[0]+x], right[y*size[0]+x]
        if len(a) != 4 or len(b) != 4:
            raise ValueError("Native pixel is not RGBA")
        active += bool(a[3] or b[3])
        active_exact += bool(a[3] or b[3]) and a == b
        red_active += bool(a[0] or b[0])
        red_exact += bool(a[0] or b[0]) and a == b
        for histogram, av, bv in zip(histograms, a, b):
            histogram[av-bv] += 1
        if a != b:
            failures.append([x, y, a, b])
    return {"samples": len(points), "exact": len(points)-len(failures),
            "alpha_union": active, "alpha_union_exact": active_exact,
            "red_union": red_active, "red_union_exact": red_exact,
            "max_channel_delta": [max(map(abs, h), default=0) for h in histograms],
            "signed_rgba_delta_histograms": [dict(sorted(h.items())) for h in histograms], "failures": failures}


def analyze_clips(captures, rectangles, baseline, size):
    if set(captures) != set(rectangles):
        raise ValueError("Missing or duplicate clip capture")
    full = clip_points((0, 0, *size), size)
    points = {key: clip_points(rect, size) for key, rect in rectangles.items()}
    clear = [[0]*4 for _ in range(size[0]*size[1])]
    clips = []
    for key in captures:
        clips.append({"clip": key, "rectangle": rectangles[key],
                      "inside_vs_baseline": compare_at(captures[key], baseline, points[key], size),
                      "outside_vs_clear": compare_at(captures[key], clear, full-points[key], size)})
    pairs = []
    for left, right in itertools.combinations(captures, 2):
        overlap = points[left] & points[right]
        pairs.append({"left_clip": left, "right_clip": right,
                      **compare_at(captures[left], captures[right], overlap, size)})
    return {"clips": clips, "overlap_pairs": pairs}


def analyze(native):
    from tools.probes.decode_jinye_clip_controls import decode

    fixture, sources, captures, matrices = decode(native)
    old_fixture, old_sources, old_captures, old_matrices = decode_old(ROOT/"evidence/importer-loud-fail/r223/native")
    assert sources == old_sources and fixture["source_graph"] == old_fixture["source_graph"]
    size = tuple(fixture["size"])
    assert size == (96, 96)
    grouped = {}
    for capture in captures:
        key = capture["source_case"], capture["cached"]
        clips = grouped.setdefault(key, {})
        assert capture["clip_id"] not in clips
        clips[capture["clip_id"]] = capture
    results = []
    full = clip_points((0, 0, *size), size)
    baseline_id = fixture["clips"].index(None)
    assert baseline_id == 0 and fixture["clips"][1] == [0, 0, *size]
    for (case_id, cached), members in grouped.items():
        spec = fixture["cases"][case_id]
        old = old_fixture["cases"][spec["base_case"]]
        assert all(spec[key] == old[key] for key in ("shape", "source", "matrix", "outer", "draw", "fill", "mask"))
        assert matrices[case_id][1:19] == old_matrices[old["id"]][1:19]
        assert set(members) == set(range(len(fixture["clips"])))
        for cid, capture in members.items():
            assert capture["clip"] == fixture["clips"][cid]
            assert capture["bounds"] == members[baseline_id]["bounds"]
        previous = old_captures[old["id"]*2+int(cached)]
        assert previous["source_case"] == old["id"] and previous["cached"] == cached
        pixels = {cid: capture["pixels"] for cid, capture in members.items()}
        rectangles = {cid: rect if rect is not None else [0, 0, *size] for cid, rect in enumerate(fixture["clips"])}
        result = analyze_clips(pixels, rectangles, pixels[baseline_id], size)
        for row in result["clips"]:
            row["declared_clip"] = fixture["clips"][row["clip"]]
        results.append({"case": case_id, "base_case": old["id"], "shape": spec["shape"],
                        "source": spec["source"], "scale": spec["draw"][0], "cached": cached,
                        "bounds": members[baseline_id]["bounds"],
                        "baseline_vs_pinned": compare_at(pixels[baseline_id], previous["pixels"], full, size), **result})
    pairs = [pair for result in results for pair in result["overlap_pairs"]]
    clips = [clip for result in results for clip in result["clips"]]
    groups = defaultdict(list)
    for result in results:
        groups[result["shape"], result["scale"], result["cached"]].append(result)
    grouped_counts = []
    for (shape, scale, cached), cases in groups.items():
        comparisons = [p for c in cases for p in c["overlap_pairs"]]
        grouped_counts.append({"shape": shape, "scale": scale, "cached": cached,
                               "nonempty_pairs": sum(p["samples"] > 0 for p in comparisons),
                               "changed_pairs": sum(p["samples"] != p["exact"] for p in comparisons),
                               "differing_pixels": sum(p["samples"]-p["exact"] for p in comparisons),
                               "max_channel_delta": [max(p["max_channel_delta"][k] for p in comparisons) for k in range(4)]})
    return {"cases": results, "groups": grouped_counts, "declared_clips": fixture["clips"],
            "baseline_images": len(results),
            "baseline_images_exact": sum(r["baseline_vs_pinned"]["exact"] == 9216 for r in results),
            "baseline_pixels": 9216*len(results),
            "baseline_pixels_exact": sum(r["baseline_vs_pinned"]["exact"] for r in results),
            "overlap_pairs": len(pairs), "overlap_pairs_empty": sum(p["samples"] == 0 for p in pairs),
            "overlap_pairs_nonempty": sum(p["samples"] > 0 for p in pairs),
            "overlap_pairs_nonempty_exact": sum(p["samples"] > 0 and p["samples"] == p["exact"] for p in pairs),
            "explicit_full_vs_omitted_images": len(results),
            "explicit_full_vs_omitted_images_exact": sum(r["clips"][1]["inside_vs_baseline"]["exact"] == 9216 for r in results),
            "explicit_full_vs_omitted_differing_pixels": sum(9216-r["clips"][1]["inside_vs_baseline"]["exact"] for r in results),
            "overlap_pairs_changed": sum(p["samples"] != p["exact"] for p in pairs),
            "overlap_samples": sum(p["samples"] for p in pairs), "overlap_exact": sum(p["exact"] for p in pairs),
            "overlap_max_channel_delta": [max(p["max_channel_delta"][k] for p in pairs) for k in range(4)],
            "outside_clip_samples": sum(c["outside_vs_clear"]["samples"] for c in clips),
            "outside_clip_nonzero": sum(c["outside_vs_clear"]["samples"]-c["outside_vs_clear"]["exact"] for c in clips),
            "source_readback_pixels_exact": sum(map(len, sources)), "matrix_readbacks_exact": len(matrices),
            "source_raw_tag_sha256": fixture["source_graph"]["raw_tag_sha256"],
            "native_fixture_sha256": hashlib.sha256((native/"fixture.json").read_bytes()).hexdigest(),
            "pinned_fixture_sha256": hashlib.sha256((ROOT/"evidence/importer-loud-fail/r223/native/fixture.json").read_bytes()).hexdigest(),
            "retained_r229_analysis_sha256": hashlib.sha256((ROOT/"evidence/importer-loud-fail/r229/analysis.json.gz").read_bytes()).hexdigest(),
            "comparison_membership_uses_output_pixels": False, "coordinate_model_tested": False,
            "candidate_admitted": False, "gpu_advance_allowed": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(",", ":"))+"\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))
