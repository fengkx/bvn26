stop();var seq=0;var phase=0;var shifts=[-128,0,128];
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function capture(label,mc,child,matrix){
 var f=child.filters;var r=[label,child.cacheAsBitmap,f.length];for(var i=0;i<f.length;i++)r.push(f[i].blurX,f[i].blurY,f[i].quality);emit("props",r.join(","));
 var b=new flash.display.BitmapData(600,400,true,0);b.draw(mc,matrix);var black=new flash.display.BitmapData(600,400,false,0);black.draw(b);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(b.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}b.dispose();black.dispose();
}
_root.onEnterFrame=function(){
 var shift=shifts[phase];var mc=_root.attachMovie("case0","source",1);mc.gotoAndStop(1);var child=mc.getInstanceAtDepth(27-16384);
 var matrix=new flash.geom.Matrix(1,0,0,1,281.549878+shift,212.4046024);var bounds=child.getBounds(mc);
 var rectangle=new flash.geom.Rectangle(bounds.xMin,bounds.yMin,bounds.xMax-bounds.xMin,bounds.yMax-bounds.yMin);
 var probe=new flash.display.BitmapData(600,400,true,0);var generated=probe.generateFilterRect(rectangle,new flash.filters.BlurFilter(15,0,3));probe.dispose();
 emit("bounds",[phase,shift,matrix.tx,matrix.ty,bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax,generated.x,generated.y,generated.width,generated.height].join(","));
 capture(phase+"-authored",mc,child,matrix);
 child.filters=[];child.cacheAsBitmap=false;capture(phase+"-clear",mc,child,matrix);
 child.cacheAsBitmap=true;capture(phase+"-cache",mc,child,matrix);
 child.filters=[new flash.filters.BlurFilter(0,0,3)];capture(phase+"-zero",mc,child,matrix);
 child.filters=[new flash.filters.BlurFilter(15,0,3)];capture(phase+"-restored",mc,child,matrix);
 mc.removeMovieClip();phase++;if(phase==shifts.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
