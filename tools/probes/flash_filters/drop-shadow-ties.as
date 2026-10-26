stop(); var seq=0;
function emit(k,v){trace("AIREF|drop-shadow-ties|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var angles=[0,90,180,-90];var distances=[0.5/256,1.5/256,31.5/256,127.5/256];var alphas=[128,255];var colors=[0,0x3366cc];var strengths=[1,3];var blurs=[0,3];
for(var a=0;a<4;a++)for(var d=0;d<4;d++)for(var aa=0;aa<2;aa++)for(var c=0;c<2;c++)for(var st=0;st<2;st++)for(var bl=0;bl<2;bl++){
 var wrap=createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(16777215,alphas[aa]*100/255);m.moveTo(8,8);m.lineTo(16,8);m.lineTo(16,16);m.lineTo(8,16);m.endFill();
 m.filters=[new flash.filters.DropShadowFilter(distances[d],angles[a],colors[c],1,blurs[bl],blurs[bl],strengths[st],1,false,false,false)];
 var b=new flash.display.BitmapData(32,32,true,0);b.draw(wrap);
 var black=new flash.display.BitmapData(32,32,false,0);black.draw(b);
 var row=[];for(var y=0;y<32;y++)for(var x=0;x<32;x++)row.push((b.getPixel32(x,y)&0xff000000)|black.getPixel(x,y));
 emit("shadow",angles[a]+","+distances[d]+","+alphas[aa]+","+colors[c]+","+strengths[st]+","+blurs[bl]+","+row.join(","));b.dispose();black.dispose();wrap.removeMovieClip();
}
emit("done","ok");fscommand("quit");
