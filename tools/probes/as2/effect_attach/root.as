stop();
_root.draws = 0;
_root.effectRandom = function() {
   _root.draws++;
   trace("EFFECT_ATTACH|random|" + _root.draws);
   return 0.25;
};
this.createEmptyMovieClip("layer",1);
trace("EFFECT_ATTACH|before");
layer.attachMovie("effect","fx",1);
layer.fx._x = 100;
layer.fx._y = 200;
layer.fx._xscale = -100;
trace("EFFECT_ATTACH|after|" + _root.draws + "|" + layer.fx._x + "|" + layer.fx._y);
_root.onEnterFrame = function() {
   trace("EFFECT_ATTACH|next|" + _root.draws + "|" + layer.fx._x + "|" + layer.fx._y);
   trace("EFFECT_ATTACH|done");
   fscommand("quit");
};
