"""Subset a redistributable Sarasa font for menu hints; run with fontTools installed."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'godot/generated/main/title_menu'

def build(path, number, license_path):
    font = TTFont(path, fontNumber=number)
    family = font['name'].getDebugName(1)
    assert family == 'Sarasa UI SC', family
    license_text = license_path.read_text()
    assert 'SIL Open Font License, Version 1.1' in license_text
    source = (OUT/'controller.gd').read_text()
    text = ''.join(re.findall(r'hint = "([^"]+)"', source)) + ''.join(chr(i) for i in range(32,127))
    options = subset.Options()
    options.name_IDs = [0,1,2,3,4,5,6,13,14]
    options.name_legacy = True
    tool = subset.Subsetter(options=options)
    tool.populate(text=text)
    tool.subset(font)
    for record in font['name'].names:
        if record.nameID in [1,3,4,6,16]:
            record.string = 'BVN Menu'.replace(' ', '' if record.nameID == 6 else ' ').encode(record.getEncoding())
    font.save(OUT/'menu-font.ttf')
    shutil.copyfile(license_path, OUT/'FONT-LICENSE.txt')
    (OUT/'font.json').write_text(json.dumps({'source_family':family,'source_font_number':number,
        'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'license_url':'https://github.com/be5invis/Sarasa-Gothic/blob/master/LICENSE',
        'characters':''.join(sorted(set(text))),
        'limit':'Original SimSun system font is not embedded in the SWF. This open font prevents missing Web glyphs; it is not pixel-identical SimSun.'},ensure_ascii=False,indent=2)+'\n')

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--font',type=Path,required=True);p.add_argument('--font-number',type=int,required=True);p.add_argument('--license',type=Path,required=True);a=p.parse_args();build(a.font,a.font_number,a.license)
