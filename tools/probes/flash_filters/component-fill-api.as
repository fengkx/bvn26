stop();var seq=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var raw=SOURCE_BYTES;var source=new flash.display.BitmapData(SOURCE_WIDTH,SOURCE_HEIGHT,true,0);
for(var y=0;y<SOURCE_HEIGHT;y++)for(var x=0;x<SOURCE_WIDTH;x++)source.setPixel32(x,y,raw[y*SOURCE_WIDTH+x]);
var blackSource=new flash.display.BitmapData(SOURCE_WIDTH,SOURCE_HEIGHT,false,0);blackSource.draw(source);
for(var y=0;y<SOURCE_HEIGHT;y++){var row=[];for(var x=0;x<SOURCE_WIDTH;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var original=_root.attachMovie("case0","original",1);original.gotoAndStop(1);var oc=original.getInstanceAtDepth(DEPTH-16384);
var asParent=_root.createEmptyMovieClip("asParent",2);var dc=asParent.createEmptyMovieClip("child",1);
var fm=new flash.geom.Matrix(1,0,0,1,FILL_X,FILL_Y);var polygon=SOURCE_CONTOUR;
dc.beginBitmapFill(source,fm,false,true);dc.moveTo(polygon[0][0],polygon[0][1]);for(var i=1;i<polygon.length;i++)dc.lineTo(polygon[i][0],polygon[i][1]);dc.lineTo(polygon[0][0],polygon[0][1]);dc.endFill();
dc.transform.matrix=oc.transform.matrix;dc.filters=oc.filters;dc.cacheAsBitmap=oc.cacheAsBitmap;
emit("fill",[fm.a,fm.b,fm.c,fm.d,fm.tx,fm.ty].join(","));
function capture(label,parent,child,draw){
 var f=child.filters;var values=[label,child._currentframe,child.cacheAsBitmap,f.length];for(var i=0;i<f.length;i++)values.push(f[i].blurX,f[i].blurY,f[i].quality);emit("props",values.join(","));
 var image=new flash.display.BitmapData(600,400,true,0);image.draw(parent,draw);var black=new flash.display.BitmapData(600,400,false,0);black.draw(image);
 for(var y=0;y<400;y++){var row=[];for(var x=0;x<600;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",label+","+y+","+row.join(","));}image.dispose();black.dispose();
}
var parents=[original,asParent];var children=[oc,dc];var labels=["tag","as"];
for(var i=0;i<2;i++){
 var parent=parents[i];var child=children[i];var draw=new flash.geom.Matrix(SCALE,0,0,SCALE,ORIGIN_X,ORIGIN_Y);var cm=child.transform.matrix;var b=child.getBounds(child);
 emit("matrix",[labels[i],draw.a,draw.d,draw.tx,draw.ty,cm.a,cm.d,cm.tx,cm.ty,b.xMin,b.yMin,b.xMax,b.yMax].join(","));
 capture(labels[i]+"-authored",parent,child,draw);child.filters=[];child.cacheAsBitmap=false;capture(labels[i]+"-clear",parent,child,draw);child.cacheAsBitmap=true;capture(labels[i]+"-cache",parent,child,draw);
}
emit("done","ok");fscommand("quit");
