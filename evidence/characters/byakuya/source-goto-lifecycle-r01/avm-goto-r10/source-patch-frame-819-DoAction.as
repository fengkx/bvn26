doZhaoHuan();
_root.__byakuyaGotoIdentity = function(clip, tag) {
    var m = clip.mian;
    var j = clip.jiao;
    var b = clip.bdmn;
    if (m != undefined) m.__byakuya_probe_sentinel = "mian:" + tag;
    if (j != undefined) j.__byakuya_probe_sentinel = "jiao:" + tag;
    if (b != undefined) b.__byakuya_probe_sentinel = "bdmn:" + tag;
    _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|identity|" + tag + "|frame=" + String(clip._currentframe) +
        "|m_same=" + String(m === _root.__byakuya_mian_ref) +
        "|j_same=" + String(j === _root.__byakuya_jiao_ref) +
        "|b_same=" + String(b === _root.__byakuya_bdmn_ref) +
        "|m_sentinel=" + String(m == undefined ? undefined : m.__byakuya_probe_sentinel) +
        "|j_sentinel=" + String(j == undefined ? undefined : j.__byakuya_probe_sentinel) +
        "|b_sentinel=" + String(b == undefined ? undefined : b.__byakuya_probe_sentinel));
};
_root.__byakuya_mian_ref = this.mian;
_root.__byakuya_jiao_ref = this.jiao;
_root.__byakuya_bdmn_ref = this.bdmn;
_root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|identity|initial|frame=" + String(this._currentframe) +
    "|m_same=true|j_same=true|b_same=true|m_sentinel=" + String(this.mian == undefined ? undefined : this.mian.__byakuya_probe_sentinel) +
    "|j_sentinel=" + String(this.jiao == undefined ? undefined : this.jiao.__byakuya_probe_sentinel) +
    "|b_sentinel=" + String(this.bdmn == undefined ? undefined : this.bdmn.__byakuya_probe_sentinel));
_root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|entry|label=招换|start=814|script=819|" + String(_currentframe));
_root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|before|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
if (_root.__byakuyaGotoProbeDone != true) {
    _root.__byakuyaGotoProbeDone = true;
    _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|A0|" + String(_currentframe));
    this.gotoAndStop("站立");
    _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|B0|" + String(_currentframe));
    this.gotoAndStop("招换");
    _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|A1|" + String(_currentframe));
    _root.__byakuyaGotoIdentity(this, "sync_after_A1");
    this.gotoAndStop("站立");
    _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|repeat_A|" + String(_currentframe));
    this.gotoAndStop("招换");
    _root.__byakuyaGotoIdentity(this, "sync_repeat_B0");
    this.gotoAndStop("招换");
    _root.__byakuyaGotoIdentity(this, "sync_repeat_B1");
    this.gotoAndStop("站立");
    _root.__byakuyaGotoIdentity(this, "sync_final_A");
    _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|after|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
}
if (_root.__byakuyaCrossTickProbeInstalled != true) {
    _root.__byakuyaCrossTickProbeInstalled = true;
    _root.__byakuyaCrossTickProbePhase = 0;
    this.onEnterFrame = function() {
        if (_root.__byakuyaCrossTickProbePhase == 0) {
            _root.__byakuyaCrossTickProbePhase = 1;
            this.gotoAndStop("站立");
            _root.__byakuyaGotoIdentity(this, "cross_tick_A");
            _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|cross_tick_A|" + String(_currentframe));
        } else if (_root.__byakuyaCrossTickProbePhase == 1) {
            _root.__byakuyaCrossTickProbePhase = 2;
            this.gotoAndStop("招换");
            _root.__byakuyaGotoIdentity(this, "cross_tick_B");
            _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|cross_tick_B|" + String(_currentframe));
        } else if (_root.__byakuyaCrossTickProbePhase == 2) {
            _root.__byakuyaCrossTickProbePhase = 3;
            this.gotoAndStop("站立");
            _root.__byakuyaGotoIdentity(this, "cross_tick_A2");
            _root.aiEvent("AIREF|byakuya-avm-goto-r10-20260921|goto|cross_tick_A2|" + String(_currentframe));
            _root.aiGotoDone();
            this.onEnterFrame = null;
        }
    };
}
