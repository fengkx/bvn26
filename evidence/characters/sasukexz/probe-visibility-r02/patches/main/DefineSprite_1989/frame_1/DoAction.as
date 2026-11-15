function lf()
{
   if(_root.loadingFunc == undefined)
   {
      return true;
   }
   return _root.loadingFunc();
}
_root.loadingGame = true;

_root.aiGeoStamp(this, "game/main.swf#DefineSprite_1989/frame_1/DoAction.as");
