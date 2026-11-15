if(_root.game.p1.mc.hp == _root.game.p2.mc.hp)
{
   gotoAndStop("drawgame");
   play();
}
else
{
   gotoAndStop("winner");
   play();
}

_root.aiGeoStamp(this, "game/main.swf#DefineSprite_1858/frame_84/DoAction.as");
