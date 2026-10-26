stop();var seq=0;
function emit(k,v){trace("AIREF|blend-layered|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function square(p,n,d,c,a){var m=p.createEmptyMovieClip(n,d);m.beginFill(c,a*100/255);m.moveTo(0,0);m.lineTo(8,0);m.lineTo(8,8);m.lineTo(0,8);m.endFill();return m;}
var backs=[0x3366cc,0x007fff,0x80ff01];var fronts=[0xcc80aa,0xff8000,0x407ffe];var alphas=[64,128,192,255];var modes=["difference","overlay"];
for(var mode=0;mode<2;mode++)for(var pair=0;pair<3;pair++)for(var ba=0;ba<4;ba++)for(var fa=0;fa<4;fa++)for(var op=0;op<2;op++){
 var w=createEmptyMovieClip("w",1);var bg=w.createEmptyMovieClip("bg",1);square(bg,"under",1,0x203040,255);square(bg,"back",2,backs[pair],alphas[ba]);
 var g=w.createEmptyMovieClip("g",2);g.blendMode=modes[mode];g._alpha=op?100:50;square(g,"front",1,fronts[pair],alphas[fa]);
 var b=new flash.display.BitmapData(8,8,true,0);b.draw(w);var black=new flash.display.BitmapData(8,8,false,0);black.draw(b);
 emit("layered",mode+","+pair+","+alphas[ba]+","+alphas[fa]+","+(op?100:50)+","+b.getPixel32(4,4)+","+black.getPixel32(4,4));
 b.dispose();black.dispose();w.removeMovieClip();
}emit("done","ok");fscommand("quit");
