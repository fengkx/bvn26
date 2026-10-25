stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(60,8,true,0);
for(var y=0;y<8;y++){var row=[];for(var x=0;x<60;x++){var p=4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113;source.setPixel32(x,y,p);row.push(source.getPixel32(x,y));}emit("source",y+","+row.join(","));}
var minima=[-0.5,0,0.25,0.5];var origins=[-0.5,0.5];
var identity=[1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0];
var reveal=[0,0,0,0,37,0,0,0,0,73,0,0,0,0,113,0,0,0,0,255];
_root.onEnterFrame=function(){
 var minimum=minima[phase];
 for(var oi=0;oi<origins.length;oi++)for(var state=0;state<3;state++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(minimum,0);child.lineTo(minimum+60,0);child.lineTo(minimum+60,8);child.lineTo(minimum,8);child.lineTo(minimum,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(7,0,0,1,origins[oi],0);child.cacheAsBitmap=true;
  if(state>0)child.filters=[new flash.filters.ColorMatrixFilter(state==1?identity:reveal)];
  var bounds=child.getBounds(parent);var inner=child.transform.matrix;
  emit("case",[id++,minimum,origins[oi],state,inner.a,inner.tx,bounds.xMin,bounds.xMax,child.cacheAsBitmap,child.filters.length].join(","));
  if(state>0)emit("matrix",child.filters[0].matrix.join(","));
  var target=new flash.display.BitmapData(800,16,true,0);target.draw(parent,new flash.geom.Matrix(1,0,0,1,128,4));
  for(var y=0;y<16;y++){var row=[];for(var x=0;x<800;x++)row.push(target.getPixel32(x,y));emit("row",y+","+row.join(","));}
  target.dispose();parent.removeMovieClip();
 }
 phase++;if(phase==minima.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
