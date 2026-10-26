stop();var seq=0;
function emit(k,v){trace("AIREF|filter-color-order-r03|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var types=["glow","glow","matrix","matrix"];var alphas=[100,50,100,50];
for(var i=0;i<types.length;i++){
 var wrap=_root.createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(13402026,80);m.moveTo(40,40);m.lineTo(104,40);m.lineTo(104,104);m.lineTo(40,104);m.endFill();m._alpha=alphas[i];
 var glow=new flash.filters.GlowFilter(5362671,1,5,5,1,1,false,false);
 var color=new flash.filters.ColorMatrixFilter([-0.5946631, 1.0937881, 0.5008749, 0.0, 8.999999, 0.4649421, 0.50735843, 0.027699426, 0.0, 9.0, 0.10156211, 1.6525338, -0.75409585, 0.0, 9.000001, 0.0, 0.0, 0.0, 1.0, 0.0]);
 if(types[i]=="glow")m.filters=[glow];else if(types[i]=="matrix")m.filters=[color];else m.filters=[glow,color];
 new flash.geom.Transform(m).colorTransform=new flash.geom.ColorTransform(0,0,0,alphas[i]/100,57,148,230,0);
 var b=new flash.display.BitmapData(160,160,true,0);b.draw(wrap);
 var row="";for(var x=0;x<160;x++)row+=","+b.getPixel32(x,70);
 emit("color",types[i]+","+alphas[i]+row);
 var black=new flash.display.BitmapData(160,160,false,0);black.draw(b);
 row="";for(var x=0;x<160;x++)row+=","+black.getPixel32(x,70);
 emit("black",types[i]+","+alphas[i]+row);black.dispose();b.dispose();wrap.removeMovieClip();
}emit("done","ok");fscommand("quit");