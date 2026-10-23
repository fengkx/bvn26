stop();var seq=0;var tick=0;
function emit(k,v){trace("AIREF|numeric-goto-r06-fe701581|"+(seq++)+"|0|"+tick+"|0|"+k+"|"+v);}
var holder=createEmptyMovieClip("holder",1);var mc=holder.attachMovie("body","mc",1);
zhanting=true;mc.touch=false;mc.speed=0;
mc.gotoAndPlay(130);
emit("clock",mc._currentframe);
onEnterFrame=function(){tick++;emit("clock",mc._currentframe);if(tick>=30){delete onEnterFrame;emit("done","ok");fscommand("quit");}};
