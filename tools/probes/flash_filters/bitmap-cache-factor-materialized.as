stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function makeSource(label,width){
 var source=new flash.display.BitmapData(width,8,true,0);
 for(var y=0;y<8;y++){var row=[];for(var x=0;x<width;x++){source.setPixel32(x,y,4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113);row.push(source.getPixel32(x,y));}emit("source",label+","+width+","+y+","+row.join(","));}return source;
}
function row(label,bitmap,y){var values=[];for(var x=0;x<bitmap.width;x++)values.push(bitmap.getPixel32(x,y));emit(label,values.join(","));}
var source=makeSource("shared",16);var pairs=[[1,7],[7,1],[0.5,14],[2,3.5],[1,8],[8,1],[0.5,16],[2,4]];var origins=[-0.5,0,0.5];var shifts=[128,256.5];
_root.onEnterFrame=function(){
 var pair=pairs[phase];
 for(var oi=0;oi<origins.length;oi++)for(var ti=0;ti<shifts.length;ti++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(0,0);child.lineTo(16,0);child.lineTo(16,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(pair[0],0,0,1,0,0);parent.transform.matrix=new flash.geom.Matrix(pair[1],0,0,1,origins[oi],0);
  var outer=new flash.geom.Matrix(1,0,0,1,shifts[ti],4);var local=child.transform.matrix;var pm=parent.transform.matrix;var cm=child.transform.concatenatedMatrix;var bounds=child.getBounds(_root);
  emit("case",[id++,pair[0],pair[1],origins[oi],shifts[ti],local.a,pm.a,pm.tx,cm.a,cm.tx,bounds.xMin,bounds.xMax].join(","));
  // BitmapData.draw ignores the target's own transform, so use a parent wrapper.
  for(var boundary=0;boundary<3;boundary++){
   child.cacheAsBitmap=boundary==1;parent.cacheAsBitmap=boundary==2;emit("flags",[boundary,child.cacheAsBitmap,parent.cacheAsBitmap].join(","));
   var target=new flash.display.BitmapData(512,16,true,0);target.draw(_root,outer);row("pixels",target,7);target.dispose();
  }
  child.cacheAsBitmap=false;parent.cacheAsBitmap=false;var origin=Math.floor(bounds.xMin+shifts[ti]);
  for(var mode=0;mode<2;mode++){
   var localBitmap=new flash.display.BitmapData(160,16,true,0);
   var lm=mode==0?new flash.geom.Matrix(pm.a,0,0,1,pm.tx+shifts[ti]-origin,4):new flash.geom.Matrix(1,0,0,1,shifts[ti]-origin,4);
   emit("localMatrix",[mode,lm.a,lm.tx,lm.ty,origin].join(","));localBitmap.draw(mode==0?parent:_root,lm);row("local"+mode,localBitmap,7);
   var holder=_root.createEmptyMovieClip("holder",2);holder.attachBitmap(localBitmap,1,"auto",true);var placed=new flash.display.BitmapData(512,16,true,0);placed.draw(holder,new flash.geom.Matrix(1,0,0,1,origin,0));row("placed"+mode,placed,7);holder.removeMovieClip();placed.dispose();localBitmap.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==pairs.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
