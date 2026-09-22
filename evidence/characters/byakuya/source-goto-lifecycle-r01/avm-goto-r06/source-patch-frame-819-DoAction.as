doZhaoHuan();
_root.aiEvent("goto", "entry|label=招换|start=814|script=819|" + String(_currentframe));
_root.aiEvent("goto", "before|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
if (_root.__byakuyaGotoProbeDone != true) {
    _root.__byakuyaGotoProbeDone = true;
    _root.aiEvent("goto", "A0|" + String(_currentframe));
    this.gotoAndStop("站立");
    _root.aiEvent("goto", "B0|" + String(_currentframe));
    this.gotoAndStop("招换");
    _root.aiEvent("goto", "A1|" + String(_currentframe));
    this.gotoAndStop("站立");
    _root.aiEvent("goto", "after|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
}
if (_root.__byakuyaCrossTickProbeInstalled != true) {
    _root.__byakuyaCrossTickProbeInstalled = true;
    _root.__byakuyaCrossTickProbePhase = 0;
    this.onEnterFrame = function() {
        if (_root.__byakuyaCrossTickProbePhase == 0) {
            _root.__byakuyaCrossTickProbePhase = 1;
            this.gotoAndStop("站立");
            _root.aiEvent("goto", "cross_tick_A|" + String(_currentframe));
        } else if (_root.__byakuyaCrossTickProbePhase == 1) {
            _root.__byakuyaCrossTickProbePhase = 2;
            this.gotoAndStop("招换");
            _root.aiEvent("goto", "cross_tick_B|" + String(_currentframe));
        } else if (_root.__byakuyaCrossTickProbePhase == 2) {
            _root.__byakuyaCrossTickProbePhase = 3;
            this.gotoAndStop("站立");
            _root.aiEvent("goto", "cross_tick_A2|" + String(_currentframe));
            _root.aiEvent("done", "goto_complete");
            this.onEnterFrame = null;
        }
    };
}
