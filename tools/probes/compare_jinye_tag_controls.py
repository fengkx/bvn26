"""Compare preserved source-tag fills with pinned Drawing API controls exactly."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_smooth_leaf import pixel_class, source_geometry
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_affine_controls import decode as decode_drawing

REFERENCE = ROOT / "evidence/importer-loud-fail/r222/native"
REFERENCE_SHA256 = {
    "fixture.json": "50a3ddc6870e52f1e3c7dca5d8dc285ffab93ecfb8ba3bd22ecc8df720a5c7ce",
    "native.log.gz": "91d2f6e73d7a57f5b4c034d080892664d590b5234aa46eed1707547d3a31dd9a",
    "build.json": "b7b6c24c2a87c3ce81e25d4be0e94d0d4cb621c46489e91dfa97b83742f4334c",
}


def compare_pixels(tag_pixels, drawing_pixels, polygon, width=96):
    if len(tag_pixels) != len(drawing_pixels):
        raise ValueError("Native API image sizes differ")
    failures = []
    differences_by_geometry = Counter()
    deltas = [Counter() for _ in range(4)]
    alpha_support = rgb_support = alpha_support_exact = rgb_support_exact = 0
    for index, (actual, expected) in enumerate(zip(tag_pixels, drawing_pixels)):
        if len(actual) != 4 or len(expected) != 4:
            raise ValueError("Native API pixel is not RGBA")
        active_alpha = actual[3] != 0 or expected[3] != 0
        active_rgb = any(actual[:3]) or any(expected[:3])
        alpha_support += active_alpha
        rgb_support += active_rgb
        alpha_support_exact += active_alpha and actual == expected
        rgb_support_exact += active_rgb and actual == expected
        delta = [a-b for a, b in zip(actual, expected)]
        for histogram, value in zip(deltas, delta):
            histogram[value] += 1
        if actual != expected:
            x, y = index % width, index // width
            geometry = pixel_class(x, y, polygon)
            differences_by_geometry[geometry] += 1
            failures.append({"x": x, "y": y, "geometry": geometry,
                             "direct_tag": actual, "drawing_api": expected, "delta": delta})
    return {"samples": len(tag_pixels), "exact": len(tag_pixels)-len(failures),
            "alpha_support_union": alpha_support, "alpha_support_union_exact": alpha_support_exact,
            "rgb_support_union": rgb_support, "rgb_support_union_exact": rgb_support_exact,
            "max_channel_delta": [max(map(abs, values), default=0) for values in deltas],
            "signed_delta_histograms": [dict(sorted(values.items())) for values in deltas],
            "differences_by_geometry": dict(differences_by_geometry), "failures": failures}


def analyze(native):
    from tools.probes.decode_jinye_tag_controls import decode as decode_tags

    for name, digest in REFERENCE_SHA256.items():
        if hashlib.sha256((REFERENCE/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Pinned Drawing API reference changed: {name}")
    old_fixture, old_sources, old_cases, old_matrices = decode_drawing(REFERENCE)
    fixture, sources, cases, matrices = decode_tags(native)
    assert fixture["cases"] == old_fixture["cases"]
    assert fixture["source_graph"] == old_fixture["source_graph"]
    assert sources == old_sources and len(sources) == 6
    assert len(cases) == len(old_cases) == 72
    assert len(matrices) == len(old_matrices) == 36
    # The tag path has no runtime property exposing the fill matrix. Compare
    # actual placement/outer/draw readbacks, retaining fill provenance separately.
    assert all(len(row) == 19 for row in matrices)
    assert [row[0] for row in matrices] == [row[0] for row in old_matrices]
    assert [row[1:] for row in matrices] == [row[7:] for row in old_matrices]
    rows = []
    for captured, previous in zip(cases, old_cases):
        assert captured["source_case"] == previous["source_case"]
        assert captured["cached"] == previous["cached"]
        spec = fixture["cases"][captured["source_case"]]
        shape = next(row for row in fixture["source_graph"]["shapes"] if row["id"] == spec["shape"])
        _, polygon = source_geometry(spec, shape)
        rows.append({"case": spec["id"], "source": spec["source"], "shape": spec["shape"],
                     "draw_scale": spec["draw"][0], "cached": captured["cached"],
                     **compare_pixels(captured["pixels"], previous["pixels"], polygon)})
    exact = sum(row["exact"] for row in rows)
    total = sum(row["samples"] for row in rows)
    groups = []
    for scale in sorted({row["draw_scale"] for row in rows}):
        for cached in (False, True):
            selected = [row for row in rows if row["draw_scale"] == scale and row["cached"] == cached]
            groups.append({"draw_scale": scale, "cached": cached,
                           "images": len(selected), "images_exact": sum(row["exact"] == row["samples"] for row in selected),
                           "samples": sum(row["samples"] for row in selected), "exact": sum(row["exact"] for row in selected),
                           "max_channel_delta": [max(row["max_channel_delta"][k] for row in selected) for k in range(4)]})
    return {"pinned_drawing_reference": str(REFERENCE.relative_to(ROOT)),
            "pinned_reference_sha256": REFERENCE_SHA256,
            "source_readback_pixels_exact": sum(map(len, sources)),
            "source_raw_tag_sha256": fixture["source_graph"]["raw_tag_sha256"],
            "placement_outer_draw_matrix_readbacks_exact": 36,
            "fill_matrix_readback_available_in_tag_api": False,
            "cases": rows, "groups": groups, "pixels_exact": exact, "pixels_total": total,
            "images_exact": sum(row["exact"] == row["samples"] for row in rows), "images_total": len(rows),
            "bounded_source_tag_equivalence_proved": exact == total,
            "general_source_tag_equivalence_proved": False,
            "source_jpeg_leaf_sampler_admitted": False, "production_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print({key: result[key] for key in ("pixels_exact", "pixels_total", "images_exact", "images_total", "bounded_source_tag_equivalence_proved")})
    raise SystemExit(0 if result["bounded_source_tag_equivalence_proved"] else 1)
