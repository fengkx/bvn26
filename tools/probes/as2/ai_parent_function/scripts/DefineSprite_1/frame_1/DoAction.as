function decide()
{
   trace("AI_PARENT_FUNCTION FUNCTION_BEFORE parent=" + _parent);
   _parent.gotoAndPlay(2);
   trace("AI_PARENT_FUNCTION AFTER_RETAINED parent_frame=" + _parent._currentframe);
   _parent.gotoAndPlay(3);
   trace("AI_PARENT_FUNCTION AFTER_REMOVED");
}
stop();
