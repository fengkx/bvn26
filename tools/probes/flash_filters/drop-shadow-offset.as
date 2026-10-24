stop();var seq=0;
function emit(k,v){trace("AIREF|drop-shadow-offset|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var angles=[0,0.7853851318359375*180/Math.PI,90];var distances=[0,1,2,5];
for(var a=0;a<angles.length;a++)for(var d=0;d<distances.length;d++){
 var wrap=createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(16777215,100);m.moveTo(8,8);m.lineTo(16,8);m.lineTo(16,16);m.lineTo(8,16);m.endFill();
 m.filters=[new flash.filters.DropShadowFilter(distances[d],angles[a],0,1,0,0,1,1,false,false,true)];
 var b=new flash.display.BitmapData(32,32,true,0);b.draw(wrap);
 var row="";for(var y=0;y<32;y++)for(var x=0;x<32;x++)row+=","+b.getPixel32(x,y);
 emit("shadow",angles[a]+","+distances[d]+row);b.dispose();wrap.removeMovieClip();
}emit("done","ok");fscommand("quit");
