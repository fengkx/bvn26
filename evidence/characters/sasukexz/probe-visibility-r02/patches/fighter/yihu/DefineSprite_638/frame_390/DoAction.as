_root.aiEvent("frame_state_enter","390," + _currentframe + "," + 动作 + "," + ql + "," + sw);
gotoAndStop("站立");
play();

_root.aiEvent("frame_state_exit","390," + _currentframe + "," + 动作 + "," + ql + "," + sw);

_root.aiGeoStamp(this, "game/fighter/yihu.swf#DefineSprite_638/frame_390/DoAction.as");
