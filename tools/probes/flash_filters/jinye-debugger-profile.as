stop();var seq=0;var spec=SPEC;var allocation=ALLOCATION;var workload=WORKLOAD;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function matrix(v){return new flash.geom.Matrix(v[0],v[1],v[2],v[3],v[4],v[5]);}
function values(m){return [m.a,m.b,m.c,m.d,m.tx,m.ty];}
function capture(label,image){
 emit("image",[label,image.width,image.height,image.transparent].join(","));var black=new flash.display.BitmapData(image.width,image.height,false,0);black.draw(image);
 for(var y=0;y<image.height;y++){var row=[];for(var x=0;x<image.width;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}black.dispose();
}
var source=flash.display.BitmapData.loadBitmap("sourceBitmap");capture("source",source);source.dispose();
var parent=_root.createEmptyMovieClip("parent",1);var cache=parent.createEmptyMovieClip("cache",1);var leaf=cache.attachMovie("leaf56","leaf",1);
leaf.transform.matrix=matrix(spec.matrix);cache.transform.matrix=matrix(spec.outer);var draw=matrix(spec.draw);var bounds=cache.getBounds(cache);
emit("matrix",values(leaf.transform.matrix).concat(values(cache.transform.matrix),values(draw),[bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax]).join(","));
var localMode=workload=="local_uncached";var regenerate=workload=="direct_cached_regenerate";cache.cacheAsBitmap=workload=="direct_cached_reuse" || regenerate;
var localMatrix=matrix(spec.matrix);localMatrix.tx-=allocation[0];localMatrix.ty-=allocation[1];
var target=new flash.display.BitmapData(localMode?allocation[2]:600,localMode?allocation[3]:400,true,0);var started=getTimer();var iterations=0;
emit("profile",workload+";actual-source;caller-sampling-only");
_root.onEnterFrame=function(){
 for(var i=0;i<1000;i++){
  if(regenerate){cache.cacheAsBitmap=false;cache.cacheAsBitmap=true;}
  target.fillRect(target.rectangle,0);if(localMode)target.draw(leaf,localMatrix);else target.draw(parent,draw);iterations++;
 }
 if(getTimer()-started>=20000){delete _root.onEnterFrame;emit("iterations",[iterations,getTimer()-started].join(","));emit("props",[workload,cache.cacheAsBitmap,cache.filters.length,leaf._currentframe].join(","));capture("final",target);target.dispose();parent.removeMovieClip();emit("done","ok");fscommand("quit");}
};
