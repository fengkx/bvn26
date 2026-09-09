stop();
this.createEmptyMovieClip("layer",1);
layer.attachMovie("effect","fx",1);
_root.tick = 0;
_root.onEnterFrame = function() {
   if(_root.tick++ == 0) {
      layer.fx.gotoAndPlay(5);
      trace("EFFECT_RENAME|after_goto|" + layer.fx._name + "|" + layer.abcd._name);
      layer.attachMovie("effect","removed",2);
      layer.removed.gotoAndPlay(5);
      layer.removed.removeMovieClip();
      trace("EFFECT_RENAME|removed|" + layer.removed._name);
      trace("EFFECT_RENAME|root_exit");
   } else {
      trace("EFFECT_RENAME|next|" + layer.fx._name + "|" + layer.abcd._name);
      trace("EFFECT_RENAME|done");
      fscommand("quit");
   }
};
