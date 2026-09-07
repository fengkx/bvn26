trace("U02 root_f2_stop");
stop();
var intervalId = setInterval(function() {
    intervalCount++;
    trace("U02 interval_" + intervalCount + " root_frame_" + _currentframe);
    if (intervalCount == 3) {
        trace("U02 play");
        play();
        clearInterval(intervalId);
    }
}, 100);
