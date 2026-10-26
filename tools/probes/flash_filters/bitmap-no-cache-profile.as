stop();var seq=0;var phase=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var source=new flash.display.BitmapData(16,8,true,0xFF717171);
var parent=_root.createEmptyMovieClip("parent",1);var child=parent.createEmptyMovieClip("child",1);
child.beginBitmapFill(source,new flash.geom.Matrix(),false,true);child.moveTo(0,0);child.lineTo(16,0);child.lineTo(16,8);child.lineTo(0,8);child.lineTo(0,0);child.endFill();
child.transform.matrix=new flash.geom.Matrix(7,0,0,1,0,0);var target=new flash.display.BitmapData(128,16,true,0);var outer=new flash.geom.Matrix(1,0,0,1,4.5,4);
emit("profile","uncached-control;no-reference-admission");
_root.onEnterFrame=function(){
 for(var i=0;i<1000;i++){
  child.cacheAsBitmap=false;child._x=(i%3-1)*0.5;child.cacheAsBitmap=false;target.fillRect(target.rectangle,0);target.draw(parent,outer);
 }
 phase++;if(phase==60){delete _root.onEnterFrame;emit("cache",child.cacheAsBitmap);emit("iterations",phase*1000);emit("checksum",target.getPixel32(16,7));emit("done","ok");fscommand("quit");}
};
