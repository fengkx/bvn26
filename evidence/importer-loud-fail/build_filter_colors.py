from pathlib import Path
import json,hashlib,subprocess,sys,struct
sys.path.insert(0,'tools/probes');from build_minimal_swf import rect,tag
out=Path('/tmp/bvn-loud-fail/filter-colors');(out/'scripts/frame_1').mkdir(parents=True,exist_ok=True);(out/'game').mkdir(exist_ok=True)
rows=json.loads(Path('/tmp/bvn-loud-fail/shipped-filters.json').read_text());import xml.etree.ElementTree as E
matrix=[float(x.text) for x in E.fromstring(rows[-1]['filters']).findall('./item/matrix/item')]
cases=[{'type':'glow','alpha':a} for a in [100,50]]+[{'type':'matrix','alpha':a} for a in [100,50]]+[{'type':'chain','alpha':100}]
run='filter-colors-r01'
code='''stop();var seq=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var types=["glow","glow","matrix","matrix","chain"];var alphas=[100,50,100,50,100];
for(var i=0;i<types.length;i++){
 var wrap=_root.createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(13402026,80);m.moveTo(40,40);m.lineTo(104,40);m.lineTo(104,104);m.lineTo(40,104);m.endFill();m._alpha=alphas[i];
 var glow=new flash.filters.GlowFilter(5362671,1,5,5,1,1,false,false);
 var color=new flash.filters.ColorMatrixFilter(MATRIX);
 if(types[i]=="glow")m.filters=[glow];else if(types[i]=="matrix")m.filters=[color];else m.filters=[glow,color];
 var b=new flash.display.BitmapData(160,160,true,0);b.draw(wrap);
 var row="";for(var x=0;x<160;x++)row+=","+b.getPixel32(x,70);
 emit("color",types[i]+","+alphas[i]+row);b.dispose();wrap.removeMovieClip();
}emit("done","ok");fscommand("quit");'''.replace('RUN',run).replace('MATRIX',json.dumps(matrix))
(out/'scripts/frame_1/DoAction.as').write_text(code)
body=rect(0,3200,0,3200)+struct.pack('<HH',30*256,1)+tag(12,b'\0')+tag(1)+tag(0)
(out/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
subprocess.run(['java','-Duser.home=/tmp/bvn-loud-fail','-Djava.awt.headless=true','-jar','/tmp/orochimaru-ffdec/ffdec-cli.jar','-importScript',str(out/'base.swf'),str(out/'game/main.swf'),str(out/'scripts')],check=True,stdout=subprocess.DEVNULL)
(out/'build.json').write_text(json.dumps({'run_id':run,'outputs_sha256':{'game/main.swf':hashlib.sha256((out/'game/main.swf').read_bytes()).hexdigest()}}))
Path('/tmp/bvn-loud-fail/filter-color-matrix.json').write_text(json.dumps(matrix))
