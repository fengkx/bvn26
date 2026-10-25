stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(16,16,true,0);
for(var y=0;y<16;y++)for(var x=0;x<16;x++)source.setPixel32(x,y,0xff000000+(8+x*15)*65536+(8+y*15)*256+73);
var blackSource=new flash.display.BitmapData(16,16,false,0);blackSource.draw(source);
for(var y=0;y<16;y++){var row=[];for(var x=0;x<16;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}blackSource.dispose();
var matrices=[[1,0,0,1],[55446/65536,-34752/65536,34752/65536,55446/65536],[62795/65536,-18755/65536,18755/65536,62795/65536],[0,1,-1,0],[1,0.25,0.5,1]];
var offsets=[0,0.25,0.5,0.75];
_root.onEnterFrame=function(){
 var m=matrices[phase];
 for(var xi=0;xi<4;xi++)for(var yi=0;yi<4;yi++)for(var origin=0;origin<2;origin++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(),false,false);child.moveTo(0,0);child.lineTo(16,0);child.lineTo(16,16);child.lineTo(0,16);child.lineTo(0,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(m[0],m[1],m[2],m[3],offsets[xi],offsets[yi]);
  var draw=new flash.geom.Matrix(1,0,0,1,origin==0?4:7.25,origin==0?10:8.75);var cm=child.transform.matrix;
  var positionsX=[10,15,20];var positionsY=[8,12,16];var lengths=[1,3,4,8];
  for(var px=0;px<positionsX.length;px++)for(var py=0;py<positionsY.length;py++)for(var li=0;li<lengths.length;li++){
   var left=positionsX[px];var yy=positionsY[py];var length=lengths[li];
   emit("sample",[id++,phase,xi,yi,origin,cm.a,cm.b,cm.c,cm.d,cm.tx,cm.ty,draw.a,draw.b,draw.c,draw.d,draw.tx,draw.ty,left,yy,length].join(","));
   var image=new flash.display.BitmapData(40,40,true,0);image.draw(parent,draw,null,null,new flash.geom.Rectangle(left,yy,length,1));var black=new flash.display.BitmapData(40,40,false,0);black.draw(image);
   var row=[];for(var x=left;x<left+length;x++)row.push(image.getPixel32(x,yy),black.getPixel32(x,yy));emit("pixels",row.join(","));
   image.dispose();black.dispose();
  }
  parent.removeMovieClip();

 }
 phase++;if(phase==matrices.length){source.dispose();delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
