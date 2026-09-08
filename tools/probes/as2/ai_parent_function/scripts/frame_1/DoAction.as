stop();
trace("AI_PARENT_FUNCTION ROOT1");
child.decide = function()
{
   trace("AI_PARENT_FUNCTION FUNCTION_BEFORE");
   _parent.gotoAndPlay(2);
   trace("AI_PARENT_FUNCTION AFTER_RETAINED");
   _parent.gotoAndPlay(3);
   trace("AI_PARENT_FUNCTION AFTER_REMOVED");
};
setTimeout(function() { trace("AI_PARENT_FUNCTION DONE"); fscommand("quit"); }, 1000);
