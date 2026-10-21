import os
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageStat

base = Path(os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"))
report = []
for folder in sorted((base / "components").iterdir()):
    if not (folder / "native.log").exists():
        continue
    dst = base / "godot" / folder.name
    if not (dst / "clocks.json").exists():
        continue
    source = {}
    pixels = {}
    for line in (folder / "native.log").read_text().splitlines():
        fields = line.split("|", 7)
        if len(fields) != 8:
            continue
        tick = int(fields[4])
        kind, value = fields[6:]
        if tick > 100:
            continue  # The declared comparison horizon is inclusive 0..100.
        if kind == "clock":
            p, f = value.rsplit(",", 1)
            source[tick, p] = int(f)
        if kind == "pixels":
            p, y, runs = value.split(",", 2)
            row = bytearray()
            for run in runs.rstrip(",").split(","):
                count, color = run.split(":")
                row.extend(int(color, 16).to_bytes(3, "big") * int(count, 16))
            assert len(row) == 1800
            pixels.setdefault((tick, p), {})[int(y)] = row
    target = {
        (r["tick"], r["path"]): r["frame"]
        for r in json.loads((dst / "clocks.json").read_text())
    }
    diff = [
        {"tick": k[0], "path": k[1], "flash": source.get(k), "godot": target.get(k)}
        for k in sorted(source.keys() | target.keys())
        if source.get(k) != target.get(k)
    ]
    imgs = []
    out = base / "comparisons" / folder.name
    out.mkdir(parents=True, exist_ok=True)
    for (tick, name), rows in pixels.items():
        assert len(rows) == 400
        src = Image.frombytes("RGB", (600, 400), b"".join(rows[y] for y in range(400)))
        src.save(out / (name + f"-{tick:03d}.native.png"))
        p = dst / (name + f"-{tick:03d}.png")
        if not p.exists():
            continue
        port = Image.open(p).convert("RGB")
        delta = ImageChops.difference(src, port)
        im = Image.new("RGB", (1200, 430), "#eeeeee")
        im.paste(src, (0, 30))
        im.paste(port, (600, 30))
        draw = ImageDraw.Draw(im)
        draw.text((8, 9), f"Native Flash 32 | {name} | tick {tick}", fill="black")
        draw.text(
            (608, 9), "Godot | same source placement and child clocks", fill="black"
        )
        im.save(out / (name + f"-{tick:03d}.png"))
        imgs.append(
            {
                "case": name,
                "tick": tick,
                "mae": sum(ImageStat.Stat(delta).mean) / 3,
                "bbox": delta.getbbox(),
                "max_error": max(v[1] for v in delta.getextrema()),
            }
        )
    r = {
        "source": folder.name,
        "clock_samples": len(source),
        "differences": diff,
        "images": imgs,
    }
    report.append(r)
    print(
        folder.name,
        len(source),
        "clock_diffs",
        len(diff),
        "images",
        len(imgs),
        "max_mae",
        max([x["mae"] for x in imgs], default=None),
        diff[:2],
    )
(base / "component-comparisons.json").write_text(json.dumps(report, indent=2) + "\n")
