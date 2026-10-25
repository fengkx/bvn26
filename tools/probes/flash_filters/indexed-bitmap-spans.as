stop();var seq=0;var phase=0;var id=0;var epoch=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var raw=SOURCE_BYTES;var source=new flash.display.BitmapData(35,65,true,0);
for(var y=0;y<65;y++)for(var x=0;x<35;x++)source.setPixel32(x,y,raw[y*35+x]);
var bs=new flash.display.BitmapData(35,65,false,0);bs.draw(source);
for(var y=0;y<65;y++){var row=[];for(var x=0;x<35;x++)row.push(source.getPixel32(x,y),bs.getPixel32(x,y));emit("source",y+","+row.join(","));}bs.dispose();
var original=_root.attachMovie("case0","original",1);original.gotoAndStop(1);var oc=original.getInstanceAtDepth(32-16384);oc.gotoAndStop(1);
var asParent=_root.createEmptyMovieClip("asParent",2);var dc=asParent.createEmptyMovieClip("child",1);var fm=new flash.geom.Matrix(1,0,0,1,16.6,-8.15);
dc.beginBitmapFill(source,fm,false,true);dc.moveTo(51.6,-8.15);dc.lineTo(51.6,56.85);dc.lineTo(16.6,56.85);dc.lineTo(16.6,-8.15);dc.lineTo(51.6,-8.15);dc.endFill();
oc.filters=[];oc.cacheAsBitmap=false;dc.filters=[];dc.cacheAsBitmap=false;
var parents=[original,asParent];var children=[oc,dc];var scales=[1,3,5];var offsets=[0,0.25,0.5,0.75];var positions=[1,7];var ypositions=[7,15];var lengths=[1,3,4,5,7,8,9,12,16,32];
_root.onEnterFrame=function(){
 var scale=scales[Math.floor(phase/16)];var xi=Math.floor((phase%16)/4);var yi=phase%4;
 for(var px=0;px<2;px++)for(var py=0;py<2;py++)for(var li=0;li<lengths.length;li++)for(var api=0;api<2;api++){
  var child=children[api];child.transform.matrix=new flash.geom.Matrix(scale,0,0,scale,-33.1,-30.7);var cm=child.transform.matrix;var draw=new flash.geom.Matrix(1,0,0,1,300.5+offsets[xi],206.35+offsets[yi]);
  var x=Math.floor(draw.tx+cm.tx+16.6*cm.a)+positions[px];var y=Math.floor(draw.ty+cm.ty-8.15*cm.d)+ypositions[py];var clip=new flash.geom.Rectangle(x,y,lengths[li],1);
  var image=new flash.display.BitmapData(600,400,true,0);image.draw(parents[api],draw,null,null,clip);var black=new flash.display.BitmapData(600,400,false,0);black.draw(image);
  var values=[id++,api,fm.tx,fm.ty,cm.a,cm.d,cm.tx,cm.ty,draw.tx,draw.ty,x,y,child._currentframe,child.cacheAsBitmap,lengths[li]];for(var offset=0;offset<lengths[li];offset++)values.push(image.getPixel32(x+offset,y),black.getPixel32(x+offset,y));emit("sample"+epoch,values.join(","));
  image.dispose();black.dispose();
 }
 phase++;if(phase==scales.length*16){
  if(epoch==0){
   var loaded=flash.display.BitmapData.loadBitmap("indexedSource");
   if(loaded==undefined){emit("error","loadBitmap undefined");delete _root.onEnterFrame;fscommand("quit");return;}
   emit("loaded",[loaded.width,loaded.height,loaded.transparent].join(","));var blackLoaded=new flash.display.BitmapData(35,65,false,0);blackLoaded.draw(loaded);
   for(var y=0;y<65;y++){var row=[];for(var x=0;x<35;x++)row.push(loaded.getPixel32(x,y),blackLoaded.getPixel32(x,y));emit("indexed_source",y+","+row.join(","));}
   blackLoaded.dispose();loaded.dispose();epoch=1;phase=0;
  }else{delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
 }
};
