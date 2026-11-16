"""Resolve narrowly reviewed absent BODY methods without dropping call sites."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def resolve_undefined_body_calls(bundle: dict, sprite: int) -> list[dict]:
    name = 'setDirect'
    prefix = f'DefineSprite_{sprite}/'
    sites = [s for s in bundle['scripts'] if s['path'].startswith(prefix)
             and re.search(r'\b' + name + r'\b', s['source'])]
    if not sites:
        return []
    if (bundle['swf_sha256'] != '21bf68e942d417b0b39e8702ae388b8146a9c275510d83125d51a4f08dd9723f'
            or sprite != 632):
        raise ValueError('Absent BODY method has no reviewed source observation')
    # Only the observed literal-argument child calls are admitted. Any newly
    # authored definition, alias, property write or root reference must fail.
    for script in bundle['scripts']:
        remainder = re.sub(r'_parent\.setDirect\((-?1)\);', '', script['source'])
        if re.search(r'\bsetDirect\b', remainder):
            raise ValueError('setDirect now has an unresolved source binding: ' + script['path'])
    main_path = ROOT / 'scripts/main.json'
    main = json.loads(main_path.read_text())
    if any('setDirect' in s['source'] for s in main['scripts']):
        raise ValueError('setDirect now has a root binding requiring compilation')
    for site in sites:
        if not re.fullmatch(r'DefineSprite_\d+/frame_\d+/PlaceObject[23]_\d+_\d+/CLIPACTIONRECORD onClipEvent\(enterFrame\)\.as', site['path']):
            raise ValueError('Unreviewed absent BODY call scope: ' + site['path'])
    return [{'name': name, 'resolution': 'undefined_body_method_returns_undefined',
             'source_bundle_sha256': hashlib.sha256(json.dumps(bundle, sort_keys=True).encode()).hexdigest(),
             'root_bundle_sha256': hashlib.sha256(main_path.read_bytes()).hexdigest(),
             'sites': [{'path': s['path'], 'sha256': hashlib.sha256(s['source'].encode()).hexdigest()}
                       for s in sites]}]
