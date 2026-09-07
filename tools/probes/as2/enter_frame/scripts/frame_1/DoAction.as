var enterCount = 0;
this.onEnterFrame = function() {
    enterCount++;
    trace("U01 onEnterFrame_" + enterCount + " root_frame_" + _currentframe);
    if (enterCount >= 4) {
        delete this.onEnterFrame;
    }
};
trace("U01 root_f1");
