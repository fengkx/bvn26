stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(60,8,true,0);
for(var y=0;y<8;y++){var row=[];for(var x=0;x<60;x++){source.setPixel32(x,y,4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113);row.push(source.getPixel32(x,y));}emit("source",y+","+row.join(","));}
var minima=[-0.55,-0.5,-0.25,-0.05,0,0.05,0.25,0.5,0.55];
var widths=[1,2,16,60];var scales=[1,2,3,5,7,8];var origins=[-0.5,0,0.5];var alphas=[1,255];
_root.onEnterFrame=function(){
 var minimum=minima[phase];
 for(var wi=0;wi<widths.length;wi++)for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++)for(var ai=0;ai<alphas.length;ai++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);var width=widths[wi];
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(minimum,0);child.lineTo(minimum+width,0);child.lineTo(minimum+width,8);child.lineTo(minimum,8);child.lineTo(minimum,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(scales[si],0,0,1,origins[oi],0);child.cacheAsBitmap=true;
  child.filters=[new flash.filters.ColorMatrixFilter([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,alphas[ai]])];
  var bounds=child.getBounds(parent);var inner=child.transform.matrix;
  emit("case",[id++,minimum,width,inner.a,inner.tx,alphas[ai],bounds.xMin,bounds.xMax,child.cacheAsBitmap,child.filters.length].join(","));
  emit("matrix",child.filters[0].matrix.join(","));
  var target=new flash.display.BitmapData(800,16,true,0);target.draw(parent,new flash.geom.Matrix(1,0,0,1,128,4));
  var row=[];var first=-1;for(var x=0;x<800;x++){var value=target.getPixel32(x,7);row.push(value);if(first<0 && value!=0)first=x;}emit("row",row.join(","));
  var column=[];for(var y=0;y<16;y++)column.push(first<0?0:target.getPixel32(first,y));emit("column",first+","+column.join(","));
  target.dispose();parent.removeMovieClip();
 }
 phase++;if(phase==minima.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
