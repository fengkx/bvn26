stop();var seq=0;var phase=0;var cases=CASES;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function matrix(v){return new flash.geom.Matrix(v[0],v[1],v[2],v[3],v[4],v[5]);}
function values(m){return [m.a,m.b,m.c,m.d,m.tx,m.ty];}
_root.onEnterFrame=function(){
 var spec=cases[phase];var parent=_root.createEmptyMovieClip("parent",1);var cache=parent.createEmptyMovieClip("cache",1);
 var leaf=cache.attachMovie("leaf"+spec.shape,"leaf",1);leaf.transform.matrix=matrix(spec.matrix);cache.transform.matrix=matrix(spec.outer);
 var draw=matrix(spec.draw);var b=cache.getBounds(cache);
 emit("matrix",[phase].concat(values(leaf.transform.matrix),values(cache.transform.matrix),values(draw),[b.xMin,b.yMin,b.xMax,b.yMax]).join(","));
 for(var mode=0;mode<2;mode++){
  cache.cacheAsBitmap=mode==1;emit("case",[phase,mode,cache.cacheAsBitmap,cache.filters.length,leaf._currentframe].join(","));
  var image=new flash.display.BitmapData(600,400,true,0);image.draw(parent,draw);var black=new flash.display.BitmapData(600,400,false,0);black.draw(image);
  for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
  image.dispose();black.dispose();
 }
 parent.removeMovieClip();phase++;if(phase==cases.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
