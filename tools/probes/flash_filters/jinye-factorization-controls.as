stop();var seq=0;var phase=0;var cases=CASES;var source=0;var clips=CLIPS;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function matrix(v){return new flash.geom.Matrix(v[0],v[1],v[2],v[3],v[4],v[5]);}
function values(m){return [m.a,m.b,m.c,m.d,m.tx,m.ty];}
var bitmap=flash.display.BitmapData.loadBitmap("sourceBitmap");emit("source_size",[bitmap.width,bitmap.height].join(","));
for(var y=0;y<40;y++){var row=[];for(var x=0;x<92;x++)row.push(bitmap.getPixel32(x,y));emit("source",source+","+y+","+row.join(","));}bitmap.dispose();
_root.onEnterFrame=function(){
 var spec=cases[phase];var parent=_root.createEmptyMovieClip("parent",1);var cache=parent.createEmptyMovieClip("cache",1);var leaf=cache.attachMovie("leaf"+spec.shape,"leaf",1);
 leaf.transform.matrix=matrix(spec.matrix);cache.transform.matrix=matrix(spec.outer);var draw=matrix(spec.draw);var bounds=cache.getBounds(cache);
 emit("matrix",[spec.id].concat(values(leaf.transform.matrix),values(cache.transform.matrix),values(draw),[bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax]).join(","));
 for(var mode=0;mode<2;mode++){
  cache.cacheAsBitmap=mode==1;
  for(var ci=0;ci<clips.length;ci++){
   var v=clips[ci];var clip=null;var kind="omitted";var rect=[0,0,192,192];
   if(v!=null){clip=new flash.geom.Rectangle(v[0],v[1],v[2],v[3]);kind="rectangle";rect=[clip.x,clip.y,clip.width,clip.height];}var bounds=cache.getBounds(cache);
   emit("case",[spec.id,mode,ci,kind,cache.cacheAsBitmap,cache.filters.length,rect[0],rect[1],rect[2],rect[3],bounds.xMin,bounds.yMin,bounds.xMax,bounds.yMax].join(","));
   var image=new flash.display.BitmapData(192,192,true,0);if(clip==null)image.draw(parent,draw);else image.draw(parent,draw,null,null,clip);var black=new flash.display.BitmapData(192,192,false,0);black.draw(image);
   for(var y=0;y<192;y++){var row=[];for(var x=0;x<192;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
   image.dispose();black.dispose();
  }
 }
 parent.removeMovieClip();phase++;if(phase==cases.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
