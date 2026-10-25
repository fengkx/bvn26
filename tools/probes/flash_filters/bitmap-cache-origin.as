stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(60,8,true,0);
for(var y=0;y<8;y++){var row=[];for(var x=0;x<60;x++){var p=4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113;source.setPixel32(x,y,p);row.push(source.getPixel32(x,y));}emit("source",y+","+row.join(","));}
var minima=[0,2,-4];var scales=[1,1.23333740234375,3];var origins=[0,0.05,0.1,0.15,0.2,0.25,0.5];var shifts=[4,4.125,4.25,4.5,132,260];
_root.onEnterFrame=function(){
 var minimum=minima[phase%3];var scale=scales[Math.floor(phase/3)];
 for(var oi=0;oi<origins.length;oi++)for(var ti=0;ti<shifts.length;ti++){
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
  child.beginBitmapFill(source,new flash.geom.Matrix(1,0,0,1,minimum,0),false,true);child.moveTo(minimum,0);child.lineTo(minimum+60,0);child.lineTo(minimum+60,8);child.lineTo(minimum,8);child.lineTo(minimum,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(scale,0,0,1,origins[oi],0);var inner=child.transform.matrix;var outer=new flash.geom.Matrix(1,0,0,1,shifts[ti],4);var bounds=child.getBounds(parent);
  emit("case",[id++,minimum,scale,origins[oi],shifts[ti],inner.a,inner.tx,bounds.xMin,bounds.xMax].join(","));
  for(var mode=0;mode<2;mode++){
   child.cacheAsBitmap=mode==1;emit("cache",[mode,child.cacheAsBitmap].join(","));
   var b=new flash.display.BitmapData(600,16,false,0);b.draw(parent,outer);var row=[];for(var x=0;x<600;x++)row.push(b.getPixel(x,7));emit(mode==0?"clear":"cached",row.join(","));b.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==9){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
