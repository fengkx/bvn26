stop();var seq=0;
function emit(k,v){trace("AIREF|filter-integer-extent-r69|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function row(id,stage,bitmap){var black=new flash.display.BitmapData(160,160,false,0);black.draw(bitmap);var values="";for(var x=0;x<160;x++)values+=","+bitmap.getPixel32(x,70)+","+black.getPixel32(x,70);emit("row",id+","+stage+values);black.dispose();}
var widths=[5,9,17,33];var origins=[40,41];var ops=[100,50];var kernels=[0,0.5,1,1.5,1.99609375,2,2.00390625,2.5,3.5,4,4.5,8];var id=0;
for(var wi=0;wi<widths.length;wi++)for(var oi=0;oi<origins.length;oi++)for(var ai=0;ai<ops.length;ai++)for(var ki=0;ki<kernels.length;ki++){
 var w=widths[wi];var left=origins[oi];var op=ops[ai];var kernel=kernels[ki];
 var wrap=_root.createEmptyMovieClip("wrap",1);var m=wrap.createEmptyMovieClip("m",1);
 m.beginFill(13402026,53);m.moveTo(left,40);m.lineTo(left+w,40);m.lineTo(left+w,104);m.lineTo(left,104);m.endFill();
 var source=new flash.display.BitmapData(w,64,true,0);source.draw(m,new flash.geom.Matrix(1,0,0,1,-left,-40));
 m.removeMovieClip();m=wrap.createEmptyMovieClip("m",1);m.attachBitmap(source,1,"auto",false);m._x=left;m._y=40;
 var b=new flash.display.BitmapData(160,160,true,0);b.draw(wrap);row(id,"input",b);b.dispose();
 var glow=new flash.filters.GlowFilter(5362671,1,kernel,kernel,1,1,false,false);
 b=new flash.display.BitmapData(160,160,true,0);var r=b.generateFilterRect(new flash.geom.Rectangle(left,40,w,64),glow);
 var filtered=new flash.display.BitmapData(r.width,r.height,true,0);
 filtered.applyFilter(source,new flash.geom.Rectangle(0,0,w,64),new flash.geom.Point(left-r.x,40-r.y),glow);
 var pad=Math.floor(kernel/2)+1;var px=left-pad;var py=40-pad;
 var padded=new flash.display.BitmapData(w+2*pad+1,64+2*pad+1,true,0);padded.copyPixels(filtered,new flash.geom.Rectangle(0,0,r.width,r.height),new flash.geom.Point(r.x-px,r.y-py));
 emit("case",id+","+w+","+left+","+op+","+kernel+","+r.x+","+r.y+","+r.width+","+r.height+","+padded.width+","+padded.height+","+px+","+py+","+glow.blurX);
 m.filters=[glow];b.draw(wrap);row(id,"implicit_filtered",b);b.dispose();
 var cx=new flash.geom.ColorTransform(0,0,0,op/100,57,148,230,0);new flash.geom.Transform(m).colorTransform=cx;
 b=new flash.display.BitmapData(160,160,true,0);b.draw(wrap);row(id,"implicit_final",b);b.dispose();
 var placement=new flash.geom.Matrix(1,0,0,1,px,py);
 b=new flash.display.BitmapData(160,160,true,0);b.draw(padded,placement);row(id,"explicit_filtered",b);b.dispose();
 b=new flash.display.BitmapData(160,160,true,0);b.draw(padded,placement,cx);row(id,"explicit_final",b);b.dispose();
 padded.dispose();filtered.dispose();source.dispose();wrap.removeMovieClip();id++;
}emit("done","ok");fscommand("quit");
