stop();var seq=0;
function emit(k,v){trace("AIREF|filter-color-raster-r03|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var colors=[13402026,1122867,11259375,8355969];var alphas=[0,1,2,10,25,50,80,99,100];
for(var c=0;c<colors.length;c++)for(var a=0;a<alphas.length;a++){
 var wrap=_root.createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(colors[c],alphas[a]);m.moveTo(40,40);m.lineTo(104,40);m.lineTo(104,104);m.lineTo(40,104);m.endFill();m.cacheAsBitmap=true;
 var b=new flash.display.BitmapData(160,160,true,0);b.draw(wrap);
 var black=new flash.display.BitmapData(160,160,false,0);black.draw(b);
 emit("raster",colors[c]+","+alphas[a]+","+b.getPixel32(70,70)+","+black.getPixel32(70,70));
 b.dispose();black.dispose();wrap.removeMovieClip();
}emit("done","ok");fscommand("quit");
