if(_root.game.p1.mc.hp > _root.game.p2.mc.hp)
{
   _root.game.p1.mc.gotoAndPlay("胜利");
}
else
{
   _root.game.p2.mc.gotoAndPlay("胜利");
}
stop();

_root.aiGeoStamp(this, "game/main.swf#DefineSprite_1844/frame_50/DoAction.as");
