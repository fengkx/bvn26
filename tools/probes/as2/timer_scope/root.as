stop();
played = 100;
timeover = {played: 0};
attachMovie("effect", "timerClip", 1);
watchdog = setInterval(function() {
   trace("TIMER_SCOPE|timeout");
   fscommand("quit");
}, 5000);
