import os
import sys, struct, subprocess, json, hashlib, uuid
from pathlib import Path

sys.path.insert(0, "tools/probes")
from build_minimal_swf import rect, tag

out = Path(
    os.path.join(os.environ.get("BVN_REVIEW_DIR", "/tmp/pain-review"), "blend-fixture")
)
(out / "game").mkdir(parents=True, exist_ok=True)
scripts = out / "scripts/frame_1"
scripts.mkdir(parents=True, exist_ok=True)
run = "blend-review-" + uuid.uuid4().hex[:10]
code = """stop();var seq=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function square(parent,name,depth,color,opacity){var m=parent.createEmptyMovieClip(name,depth);m.beginFill(color,opacity);m.moveTo(0,0);m.lineTo(8,0);m.lineTo(8,8);m.lineTo(0,8);m.endFill();return m;}
var modes=["normal","layer","multiply","screen","lighten","darken","add","subtract","hardlight"];
for(var i=0;i<modes.length;i++)for(var a=25;a<=100;a+=25){
 var wrap=_root.createEmptyMovieClip("wrap",1);square(wrap,"back",1,3368652,60);
 var group=wrap.createEmptyMovieClip("group",2);group.blendMode=modes[i];group._alpha=a;
 square(group,"a",1,13402026,70);square(group,"b",2,6728294,40);
 var pix=new flash.display.BitmapData(8,8,true,0);pix.draw(wrap);emit("blend",modes[i]+","+a+","+pix.getPixel32(4,4));pix.dispose();wrap.removeMovieClip();
}
for(var mode=0;mode<2;mode++){
 var wrap=_root.createEmptyMovieClip("wrap",1);square(wrap,"back",1,3368652,60);
 var outer=wrap.createEmptyMovieClip("outer",2);outer.blendMode="screen";outer._alpha=50;
 square(outer,"a",1,13402026,70);var inner=outer.createEmptyMovieClip("inner",2);inner.blendMode="screen";inner._alpha=50;square(inner,"b",1,6728294,40);
 if(mode==1)square(inner,"c",2,8421504,70);
 var pix=new flash.display.BitmapData(8,8,true,0);pix.draw(wrap);emit("nested",mode+","+pix.getPixel32(4,4));pix.dispose();wrap.removeMovieClip();
}
emit("done","ok");fscommand("quit");""".replace("RUN", run)
(scripts / "DoAction.as").write_text(code)
body = (
    rect(0, 320, 0, 320)
    + struct.pack("<HH", 30 * 256, 1)
    + tag(12, b"\0")
    + tag(1)
    + tag(0)
)
base = out / "base.swf"
base.write_bytes(b"FWS" + bytes([8]) + struct.pack("<I", len(body) + 8) + body)
subprocess.run(
    [
        "java",
        "-Djava.awt.headless=true",
        "-jar",
        os.environ["BVN_FFDEC"],
        "-importScript",
        str(base),
        str(out / "game/main.swf"),
        str(out / "scripts"),
    ],
    check=True,
    stdout=subprocess.DEVNULL,
)
(out / "build.json").write_text(
    json.dumps(
        {
            "run_id": run,
            "outputs_sha256": {
                "game/main.swf": hashlib.sha256(
                    (out / "game/main.swf").read_bytes()
                ).hexdigest()
            },
        },
        indent=2,
    )
)
