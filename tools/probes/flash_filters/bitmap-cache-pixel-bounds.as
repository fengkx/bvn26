stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(60,8,true,0);
for(var y=0;y<8;y++){var row=[];for(var x=0;x<60;x++){var p=4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113;source.setPixel32(x,y,p);row.push(source.getPixel32(x,y));}emit("source",y+","+row.join(","));}
function pixelBounds(label,clip){var pb=clip.transform.pixelBounds;emit(label,[typeof(pb),pb.x,pb.y,pb.width,pb.height].join(","));}
var minima=[-0.5,0,0.25,0.5];var origins=[-0.5,0.5];
_root.onEnterFrame=function(){
 var minimum=minima[phase];
 for(var oi=0;oi<origins.length;oi++)for(var route=0;route<2;route++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(minimum,0);child.lineTo(minimum+60,0);child.lineTo(minimum+60,8);child.lineTo(minimum,8);child.lineTo(minimum,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(7,0,0,1,origins[oi],0);var outer=new flash.geom.Matrix(1,0,0,1,128,4);
  if(route==1)parent.transform.matrix=outer;
  var inner=child.transform.matrix;var cm=child.transform.concatenatedMatrix;var bounds=child.getBounds(_root);
  emit("case",[id++,minimum,origins[oi],route,inner.a,inner.tx,cm.a,cm.tx,bounds.xMin,bounds.xMax].join(","));
  for(var cache=0;cache<2;cache++){
   child.cacheAsBitmap=cache==1;emit("cache",[cache,child.cacheAsBitmap].join(","));pixelBounds("before",child);
   var target=new flash.display.BitmapData(800,16,false,0);target.draw(route==0?parent:_root,route==0?outer:new flash.geom.Matrix());
   var row=[];for(var x=0;x<800;x++)row.push(target.getPixel(x,7));emit(cache==0?"clear":"cached",row.join(","));pixelBounds("after",child);target.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==minima.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
