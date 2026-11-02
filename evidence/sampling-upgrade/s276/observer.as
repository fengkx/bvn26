// Candidate observer only: compilation and native timing preservation are unproved.
_root.s276Sequence = 0;
_root.s276Observe = function(kind, owner)
{
   var menu = _root.game_menu;
   var slot = menu.getInstanceAtDepth(-16379);
   trace("S276|" + (++_root.s276Sequence) + "|" + getTimer() + "|" + kind
      + "|root=" + _root._currentframe + "|menu=" + menu._currentframe
      + "|visible=" + menu._visible + "|enabled=" + _root._menuEnabled
      + "|owner=" + owner + "|selection=" + owner._kn
      + "|slot=" + slot + "|key=" + Key.getCode()
      + "|mouseX=" + _root._xmouse + "|mouseY=" + _root._ymouse);
};
_root.s276InputObserver = {};
_root.s276InputObserver.onKeyDown = function()
{
   _root.s276Observe("native_keydown", this);
};
_root.s276InputObserver.onKeyUp = function()
{
   _root.s276Observe("native_keyup", this);
};
_root.s276InputObserver.onMouseDown = function()
{
   _root.s276Observe("native_mousedown", this);
};
_root.s276InputObserver.onMouseUp = function()
{
   _root.s276Observe("native_mouseup", this);
};
Key.addListener(_root.s276InputObserver);
Mouse.addListener(_root.s276InputObserver);
