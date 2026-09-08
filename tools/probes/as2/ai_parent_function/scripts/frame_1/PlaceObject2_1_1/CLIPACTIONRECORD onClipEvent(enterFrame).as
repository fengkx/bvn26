onClipEvent(enterFrame){
   if(!_root.checked)
   {
      _root.checked = true;
      trace("AI_PARENT_FUNCTION CALLBACK_BEFORE");
      decide();
      trace("AI_PARENT_FUNCTION CALLBACK_AFTER");
   }
}
