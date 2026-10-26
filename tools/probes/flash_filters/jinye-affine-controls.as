stop();var seq=0;var phase=0;var cases=CASES;var sources=[];
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
function matrix(v){return new flash.geom.Matrix(v[0],v[1],v[2],v[3],v[4],v[5]);}
function values(m){return [m.a,m.b,m.c,m.d,m.tx,m.ty];}
for(var ci=0;ci<6;ci++){
 var bitmap=new flash.display.BitmapData(92,40,true,0xff000000);
 for(var y=0;y<40;y++)for(var x=0;x<92;x++){
  var color=0;
  if(ci==0)color=(2*x<<16)+73;
  else if(ci==1)color=(6*y<<8)+73;
  else if(x==45+(ci-2)%2 && y==19+Math.floor((ci-2)/2))color=0xffffff;
  bitmap.setPixel32(x,y,0xff000000+color);
 }
 for(var y=0;y<40;y++){var row=[];for(var x=0;x<92;x++)row.push(bitmap.getPixel32(x,y));emit("source",ci+","+y+","+row.join(","));}
 sources.push(bitmap);
}
_root.onEnterFrame=function(){
 var spec=cases[phase];var parent=_root.createEmptyMovieClip("parent",1);var cache=parent.createEmptyMovieClip("cache",1);var leaf=cache.createEmptyMovieClip("leaf",1);
 var fill=matrix(spec.fill);leaf.beginBitmapFill(sources[spec.source],fill,false,true);leaf.moveTo(spec.mask[0][0],spec.mask[0][1]);
 for(var i=1;i<spec.mask.length;i++)leaf.lineTo(spec.mask[i][0],spec.mask[i][1]);leaf.lineTo(spec.mask[0][0],spec.mask[0][1]);leaf.endFill();
 leaf.transform.matrix=matrix(spec.matrix);cache.transform.matrix=matrix(spec.outer);var draw=matrix(spec.draw);
 emit("matrix",[phase].concat(values(fill),values(leaf.transform.matrix),values(cache.transform.matrix),values(draw)).join(","));
 for(var mode=0;mode<2;mode++){
  cache.cacheAsBitmap=mode==1;emit("case",[phase,mode,cache.cacheAsBitmap,cache.filters.length].join(","));
  var image=new flash.display.BitmapData(96,96,true,0);image.draw(parent,draw);var black=new flash.display.BitmapData(96,96,false,0);black.draw(image);
  for(var y=0;y<96;y++){var row=[];for(var x=0;x<96;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
  image.dispose();black.dispose();
 }
 parent.removeMovieClip();phase++;if(phase==cases.length){for(var i=0;i<sources.length;i++)sources[i].dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
