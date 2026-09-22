doZhaoHuan();
_root.aiEvent("AIREF|byakuya-avm-goto-r02-20260921|goto|before|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
if (_root.__byakuyaGotoProbeDone != true) {
    _root.__byakuyaGotoProbeDone = true;
    _root.aiEvent("AIREF|byakuya-avm-goto-r02-20260921|goto|A0|" + String(_currentframe));
    this.gotoAndStop("站立");
    _root.aiEvent("AIREF|byakuya-avm-goto-r02-20260921|goto|B0|" + String(_currentframe));
    this.gotoAndStop("招换");
    _root.aiEvent("AIREF|byakuya-avm-goto-r02-20260921|goto|A1|" + String(_currentframe));
    this.gotoAndStop("站立");
    _root.aiEvent("AIREF|byakuya-avm-goto-r02-20260921|goto|after|" + String(_currentframe) + "|" + String(this.mian) + "|" + String(this.jiao) + "|" + String(this.bdmn));
}
