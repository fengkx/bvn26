onClipEvent(enterFrame){
   if(!_root.checked)
   {
      _root.checked = true;
      trace("AI_PARENT_GOTO BEFORE " + this);
      _parent.gotoAndPlay(3);
      trace("AI_PARENT_GOTO AFTER_REMOVAL " + this);
      _parent.gotoAndPlay(2);
      trace("AI_PARENT_GOTO AFTER_SECOND " + this);
   }
}
