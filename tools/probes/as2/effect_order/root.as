stop();
_root.tick = 0;
_root.paused = false;
this.createEmptyMovieClip("old",1);
old.onEnterFrame = function() {
   trace("EFFECT_ORDER|old|" + _root.tick + "|" + _root.paused);
};
this.createEmptyMovieClip("layer",2);
layer.attachMovie("effect","fx",1);
_root.onEnterFrame = function() {
   trace("EFFECT_ORDER|root|" + _root.tick + "|" + _root.paused);
   if(_root.tick == 0) {
      _root.createEmptyMovieClip("late",3);
      late.onEnterFrame = function() {
         trace("EFFECT_ORDER|late|" + _root.tick + "|" + _root.paused);
      };
   }
   if(++_root.tick == 4) {
      trace("EFFECT_ORDER|done");
      fscommand("quit");
   }
};
