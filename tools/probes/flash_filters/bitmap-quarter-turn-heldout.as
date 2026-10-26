stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var w=4;var h=16;var source=new flash.display.BitmapData(w,h,true,0);var alphas=[0,64,128,255];
for(var y=0;y<h;y++)for(var x=0;x<w;x++)source.setPixel32(x,y,alphas[(x+2*y)%4]*16777216+((17+37*x+13*y)%256)*65536+((91+19*x+53*y)%256)*256+(211+11*x+7*y)%256);
var blackSource=new flash.display.BitmapData(w,h,false,0);blackSource.draw(source);
for(var y=0;y<h;y++){var row=[];for(var x=0;x<w;x++)row.push(source.getPixel32(x,y),blackSource.getPixel32(x,y));emit("source",y+","+row.join(","));}
blackSource.dispose();var scales=[3,5,7];var offsets=[0,0.25];var lengths=[3,4,5,7,8,9,12,16,24,32];
_root.onEnterFrame=function(){
 var turn=phase==0?1:3;var rw=turn%2==0?w:h;var rh=turn%2==0?h:w;
 var rotated=new flash.display.BitmapData(rw,rh,true,0);
 for(var y=0;y<h;y++)for(var x=0;x<w;x++){
  var xx=turn==0?x:(turn==1?h-1-y:(turn==2?w-1-x:y));
  var yy=turn==0?y:(turn==1?x:(turn==2?h-1-y:w-1-x));
  rotated.copyPixels(source,new flash.geom.Rectangle(x,y,1,1),new flash.geom.Point(xx,yy));
 }
 var rb=new flash.display.BitmapData(rw,rh,false,0);rb.draw(rotated);
 for(var y=0;y<rh;y++){var row=[];for(var x=0;x<rw;x++)row.push(rotated.getPixel32(x,y),rb.getPixel32(x,y));emit("rotated",turn+","+y+","+row.join(","));}rb.dispose();
 for(var si=0;si<scales.length;si++)for(var xi=0;xi<3;xi++)for(var yi=0;yi<offsets.length;yi++)for(var cached=0;cached<1;cached++)for(var mode=0;mode<1;mode++)for(var start=0;start<3;start++)for(var li=0;li<lengths.length;li++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  var matrices=[new flash.geom.Matrix(),new flash.geom.Matrix(0,1,-1,0,h,0),new flash.geom.Matrix(-1,0,0,-1,w,h),new flash.geom.Matrix(0,-1,1,0,0,w)];
  var fm=mode==0?matrices[turn]:new flash.geom.Matrix();
  child.beginBitmapFill(mode==0?source:rotated,fm,false,true);child.moveTo(0,0);child.lineTo(rw,0);child.lineTo(rw,rh);child.lineTo(0,rh);child.lineTo(0,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(scales[si],0,0,scales[si],0,0);child.cacheAsBitmap=cached==1;
  var draw=new flash.geom.Matrix(1,0,0,1,[8,-7.25,-48.5][xi],6+offsets[yi]);var cm=child.transform.matrix;var clip=new flash.geom.Rectangle([0,1,8][start],0,lengths[li],24);
  emit("case",[id++,turn,mode,child.cacheAsBitmap,cm.a,cm.d,draw.tx,draw.ty,rw,rh,fm.a,fm.b,fm.c,fm.d,fm.tx,fm.ty,clip.x,clip.width].join(","));
  var image=new flash.display.BitmapData(32,24,true,0);image.draw(parent,draw,null,null,clip);var black=new flash.display.BitmapData(32,24,false,0);black.draw(image);
  for(var y=0;y<24;y++){var row=[];for(var x=0;x<32;x++)row.push(image.getPixel32(x,y),black.getPixel32(x,y));emit("row",y+","+row.join(","));}
  image.dispose();black.dispose();parent.removeMovieClip();
 }
 rotated.dispose();phase++;if(phase==2){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
