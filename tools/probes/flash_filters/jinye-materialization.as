stop();var seq=0;var spec=SPEC;var allocation=ALLOCATION;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function matrix(v){return new flash.geom.Matrix(v[0],v[1],v[2],v[3],v[4],v[5]);}
function values(m){return [m.a,m.b,m.c,m.d,m.tx,m.ty];}
function capture(label,image){
 emit("image",[label,image.width,image.height,image.transparent].join(","));
 var black=new flash.display.BitmapData(image.width,image.height,false,0);black.draw(image);
 for(var y=0;y<image.height;y++){var row=[];for(var x=0;x<image.width;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}black.dispose();
}
var source=flash.display.BitmapData.loadBitmap("sourceBitmap");capture("source",source);source.dispose();
_root.onEnterFrame=function(){
 delete _root.onEnterFrame;
 var parent=_root.createEmptyMovieClip("parent",1);var cache=parent.createEmptyMovieClip("cache",1);var leaf=cache.attachMovie("leaf56","leaf",1);
 leaf.transform.matrix=matrix(spec.matrix);cache.transform.matrix=matrix(spec.outer);var draw=matrix(spec.draw);var bounds=cache.getBounds(cache);
 emit("matrix",values(leaf.transform.matrix).concat(values(cache.transform.matrix),values(draw),[bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax]).join(","));
 for(var mode=0;mode<2;mode++){
  cache.cacheAsBitmap=mode==1;emit("props",[mode,cache.cacheAsBitmap,cache.filters.length,leaf._currentframe].join(","));
  var direct=new flash.display.BitmapData(600,400,true,0);direct.draw(parent,draw);capture(mode+"-direct",direct);direct.dispose();
  var localMatrix=matrix(spec.matrix);localMatrix.tx-=allocation[0];localMatrix.ty-=allocation[1];
  var local=new flash.display.BitmapData(allocation[2],allocation[3],true,0);local.draw(leaf,localMatrix);
  emit("allocation",[mode].concat(allocation,values(localMatrix)).join(","));capture(mode+"-local",local);
  var materialized=_root.createEmptyMovieClip("materialized",2);var second=materialized.createEmptyMovieClip("cache",1);second.transform.matrix=matrix(spec.outer);second.cacheAsBitmap=mode==1;
  var placed=second.createEmptyMovieClip("leaf",1);placed.attachBitmap(local,1,"never",true);placed.transform.matrix=new flash.geom.Matrix(1,0,0,1,allocation[0],allocation[1]);
  var b=second.getBounds(second);emit("second",[mode,second.cacheAsBitmap].concat(values(placed.transform.matrix),values(second.transform.matrix),[b.xMin,b.yMin,b.xMax,b.yMax]).join(","));
  var output=new flash.display.BitmapData(600,400,true,0);output.draw(materialized,draw);capture(mode+"-materialized",output);output.dispose();materialized.removeMovieClip();local.dispose();
 }
 parent.removeMovieClip();emit("done","ok");fscommand("quit");
};
