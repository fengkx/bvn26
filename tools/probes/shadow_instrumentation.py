"""Read-only observations around the retained original shadow implementation."""
import re


def instrument(source: str) -> str:
    source = re.sub(r'(function showdow\(rgb\)\s*\{)', lambda m: m[1] + '\n_root.aiEvent("shadow_call", String(this) + "," + _si);', source)
    source = source.replace('_loc4_._alpha = param.alphaStart;', '''_loc4_._alpha = param.alphaStart;
   _root.aiEvent("shadow_spawn", String(mc) + "," + _loc6_ + "," + mc.mc._currentframe + "," + _loc4_._x + "," + _loc4_._y + "," + _loc4_._xscale + "," + _loc8_.width + "," + _loc8_.height + "," + _loc4_._alpha + "," + _loc5_.xMin + "," + _loc5_.yMin + "," + _loc5_.xMax + "," + _loc5_.yMax);''')
    source = source.replace('this._alpha -= param.alphaLose;', '''this._alpha -= param.alphaLose;
      _root.aiEvent("shadow_fade", String(this) + "," + this._alpha);''')
    return source
