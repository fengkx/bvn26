trace("EFFECT_ATTACH|frame1|" + _root.draws + "|" + _x + "|" + _y);
_X = _X + (_root.effectRandom() * 10 - _root.effectRandom() * 10);
_Y = _Y + (_root.effectRandom() * 20 - _root.effectRandom() * 30);
trace("EFFECT_ATTACH|exit|" + _root.draws + "|" + _x + "|" + _y);
stop();
