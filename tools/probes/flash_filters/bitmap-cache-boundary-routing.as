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
  emit("group",[id++,scale,origins[oi],shifts[ti]].join(","));
  for(var route=0;route<2;route++){
   var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
   child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(0,0);child.lineTo(16,0);child.lineTo(16,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();
   child.transform.matrix=new flash.geom.Matrix(scale,0,0,1,route==0?origins[oi]:0,0);var inner=child.transform.matrix;
   var outer=new flash.geom.Matrix(1,0,0,1,route==0?shifts[ti]:shifts[ti]+origins[oi],4);var bounds=parent.getBounds(_root);var concatenated=child.transform.concatenatedMatrix;var effective=inner.clone();effective.concat(outer);
   emit("route",[route,inner.a,inner.tx,outer.tx,concatenated.a,concatenated.tx,effective.a,effective.tx,bounds.xMin,bounds.xMax].join(","));
   for(var boundary=0;boundary<3;boundary++){
    child.cacheAsBitmap=boundary==1;parent.cacheAsBitmap=boundary==2;emit("flags",[boundary,child.cacheAsBitmap,parent.cacheAsBitmap].join(","));
    var target=new flash.display.BitmapData(512,16,true,0);target.draw(parent,outer);row("pixels",target,7);target.dispose();
   }
   parent.removeMovieClip();
  }
 }
 phase++;if(phase==2){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
