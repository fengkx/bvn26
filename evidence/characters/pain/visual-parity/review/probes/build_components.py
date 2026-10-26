import os
import re, sys, struct, zlib, json, hashlib, uuid, subprocess, collections, math
from pathlib import Path

sys.path.insert(0, "tools/probes")
from build_minimal_swf import rect, tag


def tags(body):
    offset = 0
    while offset < len(body):
        start = offset
        h = struct.unpack_from("<H", body, offset)[0]
        offset += 2
        code = h >> 6
        n = h & 63
        if n == 63:
            n = struct.unpack_from("<I", body, offset)[0]
            offset += 4
        data = body[offset : offset + n]
        offset += n
        yield code, data, body[start:offset]


def swf_tags(path):
    raw = path.read_bytes()
    b = raw[8:] if raw[:3] == b"FWS" else zlib.decompress(raw[8:])
    offset = (5 + 4 * (b[0] >> 3) + 7) // 8 + 4
    return list(tags(b[offset:]))


def bounds(row):
    d = json.loads(Path(row["timeline"]).read_text())
    defs = {v["character_id"]: v for v in d["definitions"]}

    def transform(b, m):
        a = float(m.get("scaleX", 1))
        dd = float(m.get("scaleY", 1))
        bb = float(m.get("rotateSkew0", 0))
        c = float(m.get("rotateSkew1", 0))
        tx = float(m.get("translateX", 0)) / 20
        ty = float(m.get("translateY", 0)) / 20
        pts = [
            (a * x + c * y + tx, bb * x + dd * y + ty)
            for x in [b[0], b[2]]
            for y in [b[1], b[3]]
        ]
        return [
            min(v[0] for v in pts),
            min(v[1] for v in pts),
            max(v[0] for v in pts),
            max(v[1] for v in pts),
        ]

    def walk(cid, anc):
        if cid in anc:
            return None
        v = defs.get(cid, {})
        if "shape_bounds_twips" in v:
            b = v["shape_bounds_twips"]
            return [b[k] / 20 for k in ["Xmin", "Ymin", "Xmax", "Ymax"]]
        boxes = []
        for frame in v.get(
            "display_list_frames", [v.get("first_frame_display_list", [])]
        ):
            for p in frame:
                b = walk(p["character_id"], anc + [cid])
                if b:
                    boxes.append(transform(b, p.get("matrix", {})))
        if not boxes:
            return None
        return [
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        ]

    b = walk(row["symbol"], [])
    if b and row["kind"] == "blend":
        b = transform(b, row["placement"].get("matrix", {}))
    if not b or b[2] <= b[0] or b[3] <= b[1]:
        return {"scale": 1, "x": 300, "y": 200, "bounds": b}
    s = min(1, 500 / (b[2] - b[0]), 300 / (b[3] - b[1]))
    return {
        "scale": s,
        "x": 300 - (b[0] + b[2]) * s / 2,
        "y": 200 - (b[1] + b[3]) * s / 2,
        "bounds": b,
    }


rows = json.loads(
    Path(
        os.path.join(
            os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"), "inventory.json"
        )
    ).read_text()
)
groups = collections.defaultdict(list)
for r in rows:
    r["normalization"] = bounds(r)
    if r["kind"] == "clock":
        fs = [x["frame"] for x in r["controls"]] or [10, 20, 99]
        r["samples"] = sorted(
            set(
                [0]
                + [max(0, f - 2) for f in fs]
                + [f - 1 for f in fs]
                + [min(100, f + 2) for f in fs]
            )
        )
    else:
        r["samples"] = sorted(
            set(
                [
                    0,
                    r["frame_count"] // 2,
                    max(0, r["frame_count"] - 1),
                    min(100, r["frame_count"] + 2),
                ]
            )
        )
    groups[r["source"]["path"]].append(r)
root = Path(
    os.path.join(os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"), "components")
)
root.mkdir(exist_ok=True)
for src, tests in groups.items():
    source = Path(src)
    name = source.stem if src != "game/main.swf" else "main"
    folder = root / name
    (folder / "game").mkdir(parents=True, exist_ok=True)
    (folder / "scripts/frame_1").mkdir(parents=True, exist_ok=True)
    original = swf_tags(source)
    sprites = {
        struct.unpack_from("<H", data)[0]: list(tags(data[4:]))
        for code, data, _ in original
        if code == 39
    }
    sprites[0] = original
    defs = b"".join(
        raw
        for code, data, raw in original
        if code not in [0, 1, 9, 12, 26, 28, 43, 56, 59, 69, 70, 76, 82, 86]
    )
    exports = []
    wrappers = []
    for i, r in enumerate(tests):
        cid = 60000 + i
        r["wrapper_symbol"] = cid
        if r["kind"] == "clock":
            place = tag(
                26, b"\x26" + struct.pack("<HH", 1, r["symbol"]) + b"\x00item\x00"
            )
            r["placement"] = {
                "character_id": r["symbol"],
                "depth": 1,
                "placed_frame": 1,
                "name": "item",
            }
        else:
            # Recreate this authored placement's exact tag state, including MOVE deltas.
            frame = 1
            span = []
            for code, data, raw in sprites[r["owner"]]:
                if code == 1:
                    if frame == r["source_frame"]:
                        break
                    frame += 1
                if code not in [26, 70, 28]:
                    continue
                depth = struct.unpack_from(
                    "<H", data, 0 if code == 28 else (2 if code == 70 else 1)
                )[0]
                if depth != r["placement"]["depth"]:
                    continue
                if code == 28:
                    span = []
                else:
                    if data[0] & 2 and not data[0] & 1:
                        span = []
                    span.append(raw)
            place = b"".join(span)
            assert place
        wrapper = struct.pack("<HH", cid, 2) + place + tag(1) + tag(1) + tag(0)
        wrappers.append(tag(39, wrapper))
        exports.append(struct.pack("<H", cid) + ("case" + str(i)).encode() + b"\0")
    run = "component-" + name + "-" + uuid.uuid4().hex[:8]
    spec = [
        {
            "id": r["id"],
            "samples": r["samples"],
            "scale": r["normalization"]["scale"],
            "raster_input_only": r.get("raster_input_only", False),
            "depth": r["placement"]["depth"],
            "x": r["normalization"]["x"],
            "y": r["normalization"]["y"],
        }
        for r in tests
    ]
    code = """stop();var seq=0;var tick=0;var cases=SPEC;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
function clocks(mc,path){emit("clock",path+","+mc._currentframe);for(var k in mc){var c=mc[k];if(typeof(c)=="movieclip" && c._parent==mc){var depth=c.getDepth();if(depth<0)depth+=16384;clocks(c,path+"/"+depth);}}}
function capture(mc,item){
 var b=new flash.display.BitmapData(600,400,false,6316128);var m=new flash.geom.Matrix(item.scale,0,0,item.scale,item.x,item.y);b.draw(mc,m);
 for(var y=0;y<400;y++){var row="";var last=b.getPixel(0,y);var count=1;for(var x=1;x<=600;x++){var pixel=x<600?b.getPixel(x,y):-1;if(pixel==last)count++;else{row+=count.toString(16)+":"+last.toString(16)+",";count=1;last=pixel;}}emit("pixels",item.id+","+y+","+row);}b.dispose();
}
function observe(){for(var i=0;i<cases.length;i++){var mc=_root["case"+i];if(cases[i].raster_input_only){var child=mc.getInstanceAtDepth(cases[i].depth-16384);if(typeof(child)!="movieclip"){emit("input_error",cases[i].id);fscommand("quit");return;}child.filters=[];child.cacheAsBitmap=false;if(tick==0)emit("raster_input",cases[i].id+","+child.filters.length+","+child.cacheAsBitmap);}clocks(mc,cases[i].id);for(var j=0;j<cases[i].samples.length;j++)if(cases[i].samples[j]==tick)capture(mc,cases[i]);}}
for(var i=0;i<cases.length;i++){var mc=_root.attachMovie("case"+i,"case"+i,i+1);mc.gotoAndStop(1);}
observe();
_root.onEnterFrame=function(){tick++;if(tick==10 || tick==20){for(var i=0;i<cases.length;i++)_root["case"+i].gotoAndStop(tick==10?2:1);}observe();if(tick>=100){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}};
""".replace("RUN", run).replace(
        "SPEC", re.sub(r'"([a-z_]+)":', r"\1:", json.dumps(spec, separators=(",", ":")))
    )
    (folder / "scripts/frame_1/DoAction.as").write_text(code)
    body = (
        rect(0, 12000, 0, 8000)
        + struct.pack("<HH", 30 * 256, 1)
        + tag(65, struct.pack("<HH", 256, 300))
        + defs
        + b"".join(wrappers)
        + tag(56, struct.pack("<H", len(exports)) + b"".join(exports))
        + tag(12, b"\0")
        + tag(1)
        + tag(0)
    )
    base = folder / "base.swf"
    base.write_bytes(b"FWS" + bytes([8]) + struct.pack("<I", len(body) + 8) + body)
    with (folder / "build.log").open("w") as log:
        subprocess.run(
            [
                "java",
                "-Djava.awt.headless=true",
                "-jar",
                os.environ["BVN_FFDEC"],
                "-importScript",
                str(base),
                str(folder / "game/main.swf"),
                str(folder / "scripts"),
            ],
            check=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    (folder / "cases.json").write_text(
        json.dumps(tests, indent=2, ensure_ascii=False) + "\n"
    )
    (folder / "build.json").write_text(
        json.dumps(
            {
                "run_id": run,
                "source": src,
                "raster_input_only": all(r.get("raster_input_only", False) for r in tests),
                "harness_script_sha256": hashlib.sha256(code.encode()).hexdigest(),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "outputs_sha256": {
                    "game/main.swf": hashlib.sha256(
                        (folder / "game/main.swf").read_bytes()
                    ).hexdigest()
                },
                "method": "Unmodified original definition tags; exported two-frame parents retain authored placements and MOVE deltas; parent held and goto at ticks 10/20.",
            },
            indent=2,
        )
        + "\n"
    )
    print(name, len(tests), flush=True)
Path(
    os.path.join(os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"), "inventory.json")
).write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
