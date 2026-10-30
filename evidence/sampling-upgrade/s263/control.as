_global.s263Run = function()
{
   var host = _root.createEmptyMovieClip("s263Host", _root.getNextHighestDepth());
   var worker = function(witness, invalidate)
   {
      var saved = witness;
      var operation = invalidate;
      saved.before = 1;
      saved.receiverBefore = this == saved.receiver;
      operation(saved);
      saved.post = 1;
   };
   var operation = function(witness)
   {
      witness.occupiedBefore = witness.host.getInstanceAtDepth(witness.depth) == witness.receiver;
      if(witness.mode == "remove") witness.receiver.removeMovieClip();
      witness.emptyAtBoundary = witness.host.getInstanceAtDepth(witness.depth) == undefined;
      witness.boundary = 1;
   };
   var modes = ["retain", "remove"];
   for(var i = 0; i < 2; i++)
   {
      var receiver = host.createEmptyMovieClip("receiver", 1);
      receiver.run = worker;
      var witness = {mode:modes[i],host:host,receiver:receiver,depth:1,before:0,boundary:0,post:0};
      receiver.run(witness, operation);
      aiEvent("s263_register_control", witness.mode + "," + witness.before + "," + witness.receiverBefore + "," + witness.occupiedBefore + "," + witness.emptyAtBoundary + "," + witness.boundary + "," + witness.post + "," + (host.getInstanceAtDepth(1) == undefined));
      receiver.removeMovieClip();
   }
   host.removeMovieClip();
};
