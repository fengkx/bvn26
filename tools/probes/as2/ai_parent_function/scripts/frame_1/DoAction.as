stop();
trace("AI_PARENT_FUNCTION ROOT1");
setTimeout(function() { trace("AI_PARENT_FUNCTION TIMEOUT"); fscommand("quit"); }, 10000);
