if(_root.game.p1.mc.hp > _root.game.p2.mc.hp)
{
   _root.game.p2.mc.gotoAndPlay("失败");
}
else
{
   _root.game.p1.mc.gotoAndPlay("失败");
}

_root.aiGeoStamp(this, "game/main.swf#DefineSprite_1848/frame_40/DoAction.as");
