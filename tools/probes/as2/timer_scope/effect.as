stop();
played = 7;
time = function() {
   trace("TIMER_SCOPE|before|" + this + "|" + played + "|" + _root.played + "|" + _root.timeover.played);
   played = 1;
   tm = 0;
   trace("TIMER_SCOPE|after|" + played + "|" + _root.timerClip.played + "|" + _root.played + "|" + _root.timeover.played + "|" + _root.timerClip.tm);
   clearInterval(_root.timeset);
   clearInterval(_root.watchdog);
   trace("TIMER_SCOPE|done");
   fscommand("quit");
};
_root.timeset = setInterval(time,1000);
