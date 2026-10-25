stop();var seq=0;var phase=0;var id=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(60,8,true,0);
for(var y=0;y<8;y++){var row=[];for(var x=0;x<60;x++){var p=4278190080+(x%2)*255*65536+((x*37+17)%256)*256+113;source.setPixel32(x,y,p);row.push(source.getPixel32(x,y));}emit("source",y+","+row.join(","));}
var minima=[-2,-0.5,-0.25,0,0.25,0.5,2];var scales=[7,1.24481201171875];var origins=[-0.5,0,0.5];var shifts=[128,256.5];
_root.onEnterFrame=function(){
 var value=minima[phase];
 for(var mode=0;mode<3;mode++)for(var si=0;si<scales.length;si++)for(var oi=0;oi<origins.length;oi++)for(var ti=0;ti<shifts.length;ti++){
  var minimum=mode==0?-4:value;var maximum=mode==0?64:value+60;var fill=mode==2?0:value;
  var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);var fm=new flash.geom.Matrix(1,0,0,1,fill,0);
  child.beginBitmapFill(source,fm,false,true);child.moveTo(minimum,0);child.lineTo(maximum,0);child.lineTo(maximum,8);child.lineTo(minimum,8);child.lineTo(minimum,0);child.endFill();
  child.transform.matrix=new flash.geom.Matrix(scales[si],0,0,1,origins[oi],0);var inner=child.transform.matrix;var outer=new flash.geom.Matrix(1,0,0,1,shifts[ti],4);var bounds=child.getBounds(parent);
  emit("case",[id++,mode,value,minimum,maximum,fill,fm.a,fm.tx,inner.a,inner.tx,outer.tx,bounds.xMin,bounds.xMax].join(","));
  for(var cache=0;cache<2;cache++){
   child.cacheAsBitmap=cache==1;emit("cache",[cache,child.cacheAsBitmap].join(","));var target=new flash.display.BitmapData(800,16,false,0);target.draw(parent,outer);var row=[];for(var x=0;x<800;x++)row.push(target.getPixel(x,7));emit(cache==0?"clear":"cached",row.join(","));target.dispose();
  }
  parent.removeMovieClip();
 }
 phase++;if(phase==minima.length){delete _root.onEnterFrame;emit("done","ok");fscommand("quit");}
};
