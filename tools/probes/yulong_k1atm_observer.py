"""Source-bound read-only discriminator for the s239 nested receiver gap."""
import hashlib
import json
from pathlib import Path

SOURCE_PATH = 'DefineSprite_2/frame_1/DoAction.as'
SOURCE_SHA256 = 'af53d6152c07b1bcf5f72b60e581be06ffd9951b617058143d9e4c7405cde176'
TARGET = '_level0.game.p1.mc.k1atm.mian'


def validate_case(path):
    expected = Path(__file__).resolve().parents[2] / 'evidence/sampling-upgrade/s239/yulong__attack__neutral__ground__near.json'
    if path is None or json.loads(Path(path).read_text()) != json.loads(expected.read_text()):
        raise ValueError('k1atm provenance requires the unchanged s239 attack case')


def instrument_source(original, updated, name, path):
    if name != 'fighter/yulong' or path != SOURCE_PATH:
        return updated
    if hashlib.sha256(original.replace('\r\n', '\n').encode()).hexdigest() != SOURCE_SHA256:
        raise ValueError('changed Yulong nested receiver source')
    return updated + '\nif(String(this) == "' + TARGET + '") _root.aiK1Observe("source_after_stamp",this,_root.game["p" + this._parent.pn]);\n'


def instrument_geometry(source):
    needle = '      var target = _root.game["p" + mc._parent.pn];'
    if source.count(needle) != 1:
        raise ValueError('changed geometry source-list check boundary')
    return source.replace(needle, needle + '\n      if(path == "' + TARGET + '") _root.aiK1Observe("source_list_check",mc,target);', 1)
