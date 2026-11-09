// The original predicate is evaluated by the caller, once, before this forwarder.
_root.__m002ConsumerResult = function(result, consumer, serial, site)
{
   _root.__m002Emit("consumer-predicate-result", escape(consumer._target) + "," + serial + "," + site + "," + escape(result));
   return result;
};
