if(token == undefined)
{
   if(_root.registryNext == undefined) _root.registryNext = 0;
   token = ++_root.registryNext;
   trace("REGISTRY|" + _root.registryTick + "|created|" + this + "|" + token);
}
stop();
