doZhaoHuan();
_root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|entry|label=招换|start=814|script=819|" + String(_currentframe));
_root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|before|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
if (_root.__byakuyaGotoProbeDone != true) {
    _root.__byakuyaGotoProbeDone = true;
    _root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|A0|" + String(_currentframe));
    this.gotoAndStop("站立");
    _root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|B0|" + String(_currentframe));
    this.gotoAndStop("招换");
    _root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|A1|" + String(_currentframe));
    this.gotoAndStop("站立");
    _root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|after|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
}
if (_root.__byakuyaCrossTickProbeInstalled != true) {
    _root.__byakuyaCrossTickProbeInstalled = true;
    _root.__byakuyaCrossTickProbePhase = 0;
    this.onEnterFrame = function() {
        if (_root.__byakuyaCrossTickProbePhase == 0) {
            _root.__byakuyaCrossTickProbePhase = 1;
            this.gotoAndStop("站立");
            _root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|cross_tick_A|" + String(_currentframe));
        } else if (_root.__byakuyaCrossTickProbePhase == 1) {
            _root.__byakuyaCrossTickProbePhase = 2;
            this.gotoAndStop("招换");
            _root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|cross_tick_B|" + String(_currentframe));
        } else if (_root.__byakuyaCrossTickProbePhase == 2) {
            _root.__byakuyaCrossTickProbePhase = 3;
            this.gotoAndStop("站立");
            _root.aiEvent("AIREF|byakuya-avm-goto-r03-20260921|goto|cross_tick_A2|" + String(_currentframe));
            this.onEnterFrame = null;
        }
    };
}
