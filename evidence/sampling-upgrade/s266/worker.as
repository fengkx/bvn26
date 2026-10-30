stop();
var defining = this;
worker = function(witness, operation)
{
   var saved = witness;
   var invoke = operation;
   saved.before = 1;
   saved.receiverBefore = this == saved.receiver;
   saved.definingBefore = defining == saved.receiver;
   invoke(saved);
   saved.post = 1;
};
