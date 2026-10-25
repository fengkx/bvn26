stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var v=TRANSFORM;var raw=flash.display.BitmapData.loadBitmap("sourceBitmap");var materialized=new flash.display.BitmapData(137,200,true,0);var blackSource=new flash.display.BitmapData(137,200,false,0);blackSource.draw(raw);
for(var y=0;y<200;y++){var row=[];for(var x=0;x<137;x++){var p=raw.getPixel32(x,y);materialized.setPixel32(x,y,p);row.push(p,blackSource.getPixel32(x,y));}emit("source",y+","+row.join(","));}blackSource.dispose();
_root.onEnterFrame=function(){
 var storage=Math.floor(phase/2);var cached=phase%2;var parent=_root.createEmptyMovieClip("parent",1);var child;
 if(storage==0){child=parent.attachMovie("leaf","child",1);}else{child=parent.createEmptyMovieClip("child",1);child.beginBitmapFill(materialized,new flash.geom.Matrix(),false,false);child.moveTo(137,0);child.lineTo(137,200);child.lineTo(0,200);child.lineTo(0,0);child.lineTo(137,0);child.endFill();}
 child.cacheAsBitmap=cached==1;child.transform.matrix=new flash.geom.Matrix(v[0],v[1],v[2],v[3],v[4],v[5]);var cm=child.transform.matrix;var draw=new flash.geom.Matrix(1,0,0,1,v[6],v[7]);
 emit("case",[phase,storage,cached,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty,child.cacheAsBitmap,child.filters.length].join(","));
 var image=new flash.display.BitmapData(600,400,true,0);image.draw(parent,draw);var black=new flash.display.BitmapData(600,400,false,0);black.draw(image);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
 image.dispose();black.dispose();parent.removeMovieClip();phase++;if(phase==4){raw.dispose();materialized.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
