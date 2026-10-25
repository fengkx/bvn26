stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function makeSource(label,width){
 var source=new flash.display.BitmapData(width,8,true,0);
 for(var y=0;y<8;y++){var row=[];for(var x=0;x<width;x++){source.setPixel32(x,y,4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113);row.push(source.getPixel32(x,y));}emit("source",label+","+width+","+y+","+row.join(","));}return source;
}
function row(label,bitmap,y){var values=[];for(var x=0;x<bitmap.width;x++)values.push(bitmap.getPixel32(x,y));emit(label,values.join(","));}
var source=makeSource("shared",16);var scales=[5,7];var origins=[-1,-0.5,0,0.5,0.95];var shifts=[128,128.25,256.5];
_root.onEnterFrame=function(){
 var scale=scales[phase];
 for(var oi=0;oi<origins.length;oi++)for(var ti=0;ti<shifts.length;ti++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(0,0);child.lineTo(16,0);child.lineTo(16,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(scale,0,0,1,origins[oi],0);var inner=child.transform.matrix;var outer=new flash.geom.Matrix(1,0,0,1,shifts[ti],4);var bounds=child.getBounds(parent);var origin=Math.floor(bounds.xMin+shifts[ti]);
  emit("case",[id++,scale,origins[oi],shifts[ti],inner.a,inner.tx,bounds.xMin,bounds.xMax,origin].join(","));
  for(var cache=0;cache<2;cache++){
   child.cacheAsBitmap=cache==1;emit("cache",[cache,child.cacheAsBitmap].join(","));var b=new flash.display.BitmapData(512,16,true,0);b.draw(parent,outer);row(cache==0?"clear":"cached",b,7);b.dispose();
  }
  child.cacheAsBitmap=false;
  for(var mode=0;mode<2;mode++){
   var local=new flash.display.BitmapData(128,16,true,0);var matrix=mode==0?new flash.geom.Matrix(1,0,0,1,shifts[ti]-origin,4):new flash.geom.Matrix(scale,0,0,1,inner.tx+shifts[ti]-origin,4);
   emit("localMatrix",[mode,matrix.a,matrix.tx,matrix.ty,origin].join(","));local.draw(mode==0?parent:child,matrix);row("local"+mode,local,7);
   var holder=_root.createEmptyMovieClip("holder",2);holder.attachBitmap(local,1,"auto",true);var dest=new flash.display.BitmapData(512,16,true,0);dest.draw(holder,new flash.geom.Matrix(1,0,0,1,origin,0));row("placed"+mode,dest,7);holder.removeMovieClip();dest.dispose();local.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==2){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
