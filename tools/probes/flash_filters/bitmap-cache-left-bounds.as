stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function makeSource(label,width){
 var source=new flash.display.BitmapData(width,8,true,0);
 for(var y=0;y<8;y++){var row=[];for(var x=0;x<width;x++){source.setPixel32(x,y,4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113);row.push(source.getPixel32(x,y));}emit("source",label+","+width+","+y+","+row.join(","));}return source;
}
function row(label,bitmap,y){var values=[];for(var x=0;x<bitmap.width;x++)values.push(bitmap.getPixel32(x,y));emit(label,values.join(","));}
var source=makeSource("shared",16);var scales=[7,8];var origins=[-0.5,0,0.5];var shifts=[128,256.5];var minima=[0,-0.5,-1,-2,-4,-8];
_root.onEnterFrame=function(){
 var minimum=minima[phase];
 for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++)for(var ti=0;ti<shifts.length;ti++)for(var mode=0;mode<2;mode++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(0,0);child.lineTo(16,0);child.lineTo(16,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();
  if(minimum<0){child.beginFill(0x7F349A,mode==0?0:100);child.moveTo(minimum,0);child.lineTo(minimum+0.25,0);child.lineTo(minimum+0.25,8);child.lineTo(minimum,8);child.lineTo(minimum,0);child.endFill();}
  child.transform.matrix=new flash.geom.Matrix(scales[si],0,0,1,origins[oi],0);var inner=child.transform.matrix;var bounds=child.getBounds(parent);var outer=new flash.geom.Matrix(1,0,0,1,shifts[ti],4);
  emit("case",[id++,minimum,mode,scales[si],origins[oi],shifts[ti],inner.a,inner.tx,bounds.xMin,bounds.xMax].join(","));
  for(var cache=0;cache<2;cache++){
   child.cacheAsBitmap=cache==1;emit("cache",[cache,child.cacheAsBitmap].join(","));var target=new flash.display.BitmapData(512,16,true,0);target.draw(parent,outer);row(cache==0?"clear":"cached",target,7);target.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==minima.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
