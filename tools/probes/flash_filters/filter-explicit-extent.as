stop();var seq=0;
function emit(k,v){trace("AIREF|filter-explicit-extent-r64|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function row(id,stage,bitmap){var black=new flash.display.BitmapData(160,160,false,0);black.draw(bitmap);var values="";for(var x=0;x<160;x++)values+=","+bitmap.getPixel32(x,70)+","+black.getPixel32(x,70);emit("row",id+","+stage+values);black.dispose();}
var widths=[15,16,17,18,19,20,31,32,33,64];var origins=[40,41];var opacities=[100,50];var id=0;
for(var wi=0;wi<widths.length;wi++)for(var oi=0;oi<origins.length;oi++)for(var ai=0;ai<opacities.length;ai++){
 var w=widths[wi];var left=origins[oi];var opacity=opacities[ai];
 var wrap=_root.createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(13402026,80);m.moveTo(left,40);m.lineTo(left+w,40);m.lineTo(left+w,104);m.lineTo(left,104);m.endFill();
 var source=new flash.display.BitmapData(w,64,true,0);
 source.draw(m,new flash.geom.Matrix(1,0,0,1,-left,-40));
 m.removeMovieClip();m=wrap.createEmptyMovieClip("m",1);
 m.attachBitmap(source,1,"auto",false);m._x=left;m._y=40;
 var b=new flash.display.BitmapData(160,160,true,0);b.draw(wrap);row(id,"input",b);b.dispose();
 var glow=new flash.filters.GlowFilter(5362671,1,5,5,1,1,false,false);
 b=new flash.display.BitmapData(160,160,true,0);
 var r=b.generateFilterRect(new flash.geom.Rectangle(left,40,w,64),glow);
 emit("case",id+","+w+","+left+","+opacity+","+r.x+","+r.y+","+r.width+","+r.height);
 var filtered=new flash.display.BitmapData(r.width,r.height,true,0);
 filtered.applyFilter(source,new flash.geom.Rectangle(0,0,w,64),new flash.geom.Point(3,3),glow);
 var placement=new flash.geom.Matrix(1,0,0,1,r.x,r.y);
 b.draw(filtered,placement);row(id,"filtered",b);b.dispose();
 var cx=new flash.geom.ColorTransform(0,0,0,opacity/100,57,148,230,0);
 b=new flash.display.BitmapData(160,160,true,0);b.draw(filtered,placement,cx);row(id,"final",b);b.dispose();filtered.dispose();wrap.removeMovieClip();source.dispose();id++;
}emit("done","ok");fscommand("quit");
