stop();
var po = _root.getFighterData(_root.p1selt);
var txts = po.says;
wintxt.text = txts[_root.aiRandom("main#DefineSprite_2019/frame_1/DoAction.as:1") * txts.length >> 0];

_root.aiGeoStamp(this, "game/main.swf#DefineSprite_2019/frame_1/DoAction.as");
