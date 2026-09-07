var hostTick = 0;
this.onEnterFrame = function() {
    hostTick++;
    trace("U06 host_tick_" + hostTick + " timer_" + getTimer());
    if (hostTick >= 18) {
        delete this.onEnterFrame;
    }
};
createEmptyMovieClip("assistHolder", 1);
assistHolder.loadMovie("assist.swf");
trace("U06 host_load timer_" + getTimer());
stop();
