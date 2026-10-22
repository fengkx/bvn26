import sys,struct,subprocess,json,hashlib
from pathlib import Path
sys.path.insert(0,'tools/probes');from build_minimal_swf import rect,tag
out=Path('/tmp/bvn-loud-fail/filter-probe-large');(out/'game').mkdir(parents=True,exist_ok=True);(out/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
run='filter-loud-fail-large-r01'
code='''stop();var seq=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var sizes=[0,1,2,3,5,10,15,20];
for(var k=0;k<sizes.length;k++)for(var q=1;q<=3;q+=2){
 var wrap=_root.createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(16711680,100);m.moveTo(40,40);m.lineTo(104,40);m.lineTo(104,104);m.lineTo(40,104);m.endFill();
 m.filters=[new flash.filters.BlurFilter(sizes[k],0,q)];
 var b=new flash.display.BitmapData(160,160,true,0);b.draw(wrap);
 var row="";for(var x=0;x<160;x++)row+=","+b.getPixel32(x,70);
 emit("blur",sizes[k]+","+q+row);b.dispose();wrap.removeMovieClip();
}
emit("done","ok");fscommand("quit");'''.replace('RUN',run)
(out/'scripts/frame_1/DoAction.as').write_text(code)
body=rect(0,3200,0,3200)+struct.pack('<HH',30*256,1)+tag(12,b'\0')+tag(1)+tag(0)
(out/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
subprocess.run(['java','-Duser.home=/tmp/bvn-loud-fail','-Djava.awt.headless=true','-jar','/tmp/orochimaru-ffdec/ffdec-cli.jar','-importScript',str(out/'base.swf'),str(out/'game/main.swf'),str(out/'scripts')],check=True,stdout=subprocess.DEVNULL)
(out/'build.json').write_text(json.dumps({'run_id':run,'outputs_sha256':{'game/main.swf':hashlib.sha256((out/'game/main.swf').read_bytes()).hexdigest()}}))
