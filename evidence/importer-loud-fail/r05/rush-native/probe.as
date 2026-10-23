stop();var seq=0;var tick=0;
function emit(k,v){trace("AIREF|rush-r05|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
var holder=createEmptyMovieClip("holder",1);var mc=holder.attachMovie("XG_rush","fx",1);mc._x=128;mc._y=128;
function observe(){
 var alive=mc._totalframes>1;emit("clock",alive?mc._currentframe:0);
 var b=new flash.display.BitmapData(256,256,false,0);b.draw(holder);
 var row="";for(var y=64;y<=192;y+=16){for(var x=64;x<=192;x+=16){row+=b.getPixel(x,y)+",";}}emit("pixels",row);b.dispose();
}
observe();onEnterFrame=function(){tick++;observe();if(tick>=20){delete onEnterFrame;emit("done","ok");fscommand("quit");}};
