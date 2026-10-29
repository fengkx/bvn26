"""Opt-in terminal observation window for the retained s240 display case."""
import json
from pathlib import Path

HEADER = 'onEnterFrame = function()\n{\n'
FLAG = '_root.aiYulongDisplayComplete = false;\n'
GUARD = '''   if(_root.aiYulongDisplayComplete)
   {
      aiEvent("capture_window_closed", "before-next-root-increment");
      _root.onEnterFrame = function() {};
      _root.aiEvent = function() {};
      return;
   }
'''
DONE = '      aiEvent("done", "");'
ARM = '\n      _root.aiYulongDisplayComplete = true;'


def validate_case(path):
    expected = Path(__file__).resolve().parents[2] / 'evidence/sampling-upgrade/s240/yulong__attack__neutral__ground__near.json'
    if path is None or json.loads(Path(path).read_text()) != json.loads(expected.read_text()):
        raise ValueError('display completion requires the unchanged s240 case')


def instrument(bootstrap):
    if bootstrap.count(HEADER) != 1 or bootstrap.count(DONE) != 1:
        raise ValueError('missing unique display completion boundaries')
    if HEADER + '   aiDisplay++;' not in bootstrap:
        raise ValueError('changed root observation increment boundary')
    # Retain callbacks in the terminal root period. Close only when the next
    # root callback would otherwise advance counters, inputs and samples.
    return bootstrap.replace(HEADER, FLAG + HEADER + GUARD, 1).replace(DONE, DONE + ARM, 1)
