stop();var seq=0;var phase=0;var shifts=[-128,-17,-1,0,1,17,128];
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function readback(label,b){
 var black=new flash.display.BitmapData(600,400,false,0);black.draw(b);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(b.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}
 black.dispose();
}
_root.onEnterFrame=function(){
 var shift=shifts[phase];var mc=_root.attachMovie("case0","source",1);mc.gotoAndStop(1);var child=mc.getInstanceAtDepth(27-16384);
 var matrix=new flash.geom.Matrix(1,0,0,1,281.549878+shift,212.4046024);var inner=child.transform.matrix;var bounds=child.getBounds(mc);var f=child.filters[0];
 emit("props",[phase,shift,matrix.a,matrix.d,matrix.tx,matrix.ty,inner.a,inner.d,inner.tx,inner.ty,bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax,f.blurX,f.blurY,f.quality].join(","));
 var authored=new flash.display.BitmapData(600,400,true,0);authored.draw(mc,matrix);readback(phase+"-authored",authored);authored.dispose();
 child.filters=[];child.cacheAsBitmap=false;var input=new flash.display.BitmapData(600,400,true,0);input.draw(mc,matrix);readback(phase+"-input",input);input.dispose();mc.removeMovieClip();
 phase++;if(phase==shifts.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
