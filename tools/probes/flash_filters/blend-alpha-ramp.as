stop();
var seq=0;
function emit(k,v) {trace("AIREF|blend-alpha-ramp|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function square(parent,name,depth,color,alpha) {
 var m=parent.createEmptyMovieClip(name,depth);m.beginFill(color,alpha*100/255);
 m.moveTo(0,0);m.lineTo(2,0);m.lineTo(2,2);m.lineTo(0,2);m.endFill();return m;
}
var backs=[0x3366cc,0x007fff,0x80ff01];var fronts=[0xcc80aa,0xff8000,0x407ffe];
var modes=["difference","overlay"];var backAlphas=[153,255];
for(var mode=0;mode<2;mode++)for(var pair=0;pair<3;pair++)for(var ba=0;ba<2;ba++)for(var fa=0;fa<256;fa++) {
 var w=createEmptyMovieClip("w",1);square(w,"back",1,backs[pair],backAlphas[ba]);
 var g=w.createEmptyMovieClip("g",2);g.blendMode=modes[mode];square(g,"front",1,fronts[pair],fa);
 var b=new flash.display.BitmapData(2,2,true,0);var black=new flash.display.BitmapData(2,2,false,0);var row=[];
 b.draw(w.back);row.push(b.getPixel32(0,0));black.draw(b);row.push(black.getPixel32(0,0));
 b.fillRect(b.rectangle,0);black.fillRect(black.rectangle,0);
 b.draw(g.front);row.push(b.getPixel32(0,0));black.draw(b);row.push(black.getPixel32(0,0));
 b.fillRect(b.rectangle,0);black.fillRect(black.rectangle,0);
 b.draw(w);row.push(b.getPixel32(0,0));black.draw(b);row.push(black.getPixel32(0,0));
 emit("blend",mode+","+pair+","+backAlphas[ba]+","+fa+","+row.join(","));
 b.dispose();black.dispose();w.removeMovieClip();
}
emit("done","ok");fscommand("quit");
