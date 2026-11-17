_root.loop++;
duplicateMovieClip(_root.game.xgch,"xgch" + _root.loop,16384 + _root.loop);
_root.game["xgch" + _root.loop]._x = _parent._x;
_root.game["xgch" + _root.loop]._xscale = _parent._xscale;
_root.game["xgch" + _root.loop]._y = _parent._y;
_root.game["xgch" + _root.loop].gotoAndStop(2);

_root.aiGeoStamp(this, "game/fighter/yihu.swf#DefineSprite_1180/frame_304/DoAction.as");
