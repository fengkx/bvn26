stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function makeSource(label,width){
 var source=new flash.display.BitmapData(width,8,true,0);
 for(var y=0;y<8;y++){var row=[];for(var x=0;x<width;x++){source.setPixel32(x,y,4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113);row.push(source.getPixel32(x,y));}emit("source",label+","+width+","+y+","+row.join(","));}return source;
}
var shared=makeSource("shared",64);var widths=[16,32,35,36,37,38,60,64];var scales=[5,7];var origins=[-0.95,0,0.55,0.95];var shifts=[128,256.5];
_root.onEnterFrame=function(){
 var width=widths[phase];var narrow=makeSource(phase,width);
 for(var mode=0;mode<3;mode++)for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++)for(var ti=0;ti<shifts.length;ti++){
  var source=mode==0?narrow:shared;var painted=mode==2?16:width;
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(0,0);child.lineTo(painted,0);child.lineTo(painted,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();
  if(mode==2){child.beginFill(0,0);child.moveTo(width-1,0);child.lineTo(width,0);child.lineTo(width,8);child.lineTo(width-1,8);child.lineTo(width-1,0);child.endFill();}
  child.transform.matrix=new flash.geom.Matrix(scales[si],0,0,1,origins[oi],0);var inner=child.transform.matrix;var outer=new flash.geom.Matrix(1,0,0,1,shifts[ti],4);var bounds=child.getBounds(parent);
  emit("case",[id++,width,mode,source.width,scales[si],origins[oi],shifts[ti],inner.a,inner.tx,bounds.xMin,bounds.xMax,painted].join(","));
  for(var cache=0;cache<2;cache++){
   child.cacheAsBitmap=cache==1;emit("cache",[cache,child.cacheAsBitmap].join(","));var b=new flash.display.BitmapData(1024,16,false,0);b.draw(parent,outer);var row=[];for(var x=0;x<1024;x++)row.push(b.getPixel(x,7));emit(cache==0?"clear":"cached",row.join(","));b.dispose();
  }
  parent.removeMovieClip();
 }
 narrow.dispose();phase++;if(phase==widths.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
