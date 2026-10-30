_global.s266Run = function()
{
   var operation = function(witness)
   {
      witness.occupiedBefore = witness.host.getInstanceAtDepth(witness.depth) == witness.receiver;
      witness.host.gotoAndStop(witness.target);
      witness.emptyAtBoundary = witness.host.getInstanceAtDepth(witness.depth) == undefined;
      witness.parentFrame = witness.host._currentframe;
      witness.boundary = 1;
   };
   var hosts = [_root.s266Retain, _root.s266Remove];
   var modes = ["retain", "remove"];
   for(var i = 0; i < 2; i++)
   {
      var host = hosts[i];
      var receiver = host.child;
      var witness = {mode:modes[i],host:host,receiver:receiver,target:i + 2,depth:receiver.getDepth(),before:0,boundary:0,post:0};
      receiver.worker(witness, operation);
      aiEvent("s266_authored_control", witness.mode + "," + witness.before + "," + witness.receiverBefore + "," + witness.definingBefore + "," + witness.occupiedBefore + "," + witness.emptyAtBoundary + "," + witness.parentFrame + "," + witness.depth + "," + witness.boundary + "," + witness.post + "," + (host.getInstanceAtDepth(witness.depth) == undefined));
   }
};
