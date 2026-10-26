stop();var seq=0;
function emit(k,v){trace("AIREF|blend-alpha-boundaries|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function square(p,n,d,c,a){var m=p.createEmptyMovieClip(n,d);m.beginFill(c,a*100/255);m.moveTo(0,0);m.lineTo(8,0);m.lineTo(8,8);m.lineTo(0,8);m.endFill();return m;}
var bas=[0,2,64,128,254,255];var fas=[0,1,128,255];var grays=[0,1,64,127,128,254,255];var modes=["difference","overlay"];
for(var m=0;m<2;m++)for(var ba=0;ba<6;ba++)for(var fa=0;fa<4;fa++)for(var c=0;c<7;c++){
 var w=createEmptyMovieClip("w",1);square(w,"back",1,0x808080,bas[ba]);var g=w.createEmptyMovieClip("g",2);g.blendMode=modes[m];square(g,"front",1,grays[c]*65793,fas[fa]);
 var b=new flash.display.BitmapData(8,8,true,0);var black=new flash.display.BitmapData(8,8,false,0);var row=[];
 b.draw(w.back);row.push(b.getPixel32(4,4));black.draw(b);row.push(black.getPixel32(4,4));b.fillRect(b.rectangle,0);black.fillRect(black.rectangle,0);
 b.draw(g.front);row.push(b.getPixel32(4,4));black.draw(b);row.push(black.getPixel32(4,4));b.fillRect(b.rectangle,0);black.fillRect(black.rectangle,0);
 b.draw(w);row.push(b.getPixel32(4,4));black.draw(b);row.push(black.getPixel32(4,4));
 emit("boundary",m+","+grays[c]+","+bas[ba]+","+fas[fa]+","+row.join(","));b.dispose();black.dispose();w.removeMovieClip();
}emit("done","ok");fscommand("quit");
