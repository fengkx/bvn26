"""Source-bound block-entry instrumentation, not statement/call coverage."""
import hashlib
import json
import re

FRAME_ACTION = re.compile(r'(?:DefineSprite_(\d+)/)?frame_(\d+)/DoAction.as')

CLIP_ACTION = re.compile(r'(?:DefineSprite_(\d+)/)?frame_(\d+)/(PlaceObject[23]_\d+_\d+)/CLIPACTIONRECORD onClipEvent\((enterFrame|load)\).as')


def inventory(bundle, include_clip=False):
    records = []
    seen = set()
    for script in bundle['scripts']:
        path = script['path']
        if path in seen:
            raise ValueError('ambiguous source script path: ' + path)
        seen.add(path)
        match = FRAME_ACTION.fullmatch(path)
        record = {'swf': bundle['game_file'], 'swf_sha256': bundle['swf_sha256'],
                  'path': path, 'source_sha256': hashlib.sha256(script['source'].encode()).hexdigest(),
                  'kind': 'DoAction' if match else 'other_action',
                  'sprite': int(match[1] or 0) if match else None,
                  'frame': int(match[2]) if match else None,
                  'instrumented': bool(match and bundle['game_file'] != 'game/main.swf')}
        clip = CLIP_ACTION.fullmatch(path) if include_clip else None
        if clip:
            record.update(kind='clip_action', sprite=int(clip[1] or 0), frame=int(clip[2]),
                          placement_path=clip[3], event=clip[4],
                          instrumented=bundle['game_file'] != 'game/main.swf')
        record['id'] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        records.append(record)
    return records


def instrument(source, record):
    if not record['instrumented']:
        return source
    if record['kind'] == 'clip_action':
        header = re.compile(r'^(\s*onClipEvent\(\s*' + re.escape(record['event']) + r'\s*\)\s*\{)')
        match = header.match(source)
        if match is None or not source.rstrip().endswith('}'):
            raise ValueError('unsupported clip-action wrapper: ' + record['path'])
        event = ('\n_root.aiEvent("clipaction_entry", "' + record['id'] +
                 '," + escape(String(this)) + "," + _currentframe);\n')
        return source[:match.end()] + event + source[match.end():]
    # Only entry into the authored block is observed. Function declarations
    # and untaken branches must not be counted as calls executed.
    return ('_root.aiEvent("doaction_entry", "' + record['id'] + '," + escape(String(this)) + "," + _currentframe);\n' + source)
