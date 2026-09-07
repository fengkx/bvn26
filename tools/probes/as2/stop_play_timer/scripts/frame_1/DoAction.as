var enterCount = 0;
var intervalCount = 0;
this.onEnterFrame = function() {
    enterCount++;
    trace("U02 onEnterFrame_" + enterCount + " root_frame_" + _currentframe);
};
trace("U02 root_f1");
