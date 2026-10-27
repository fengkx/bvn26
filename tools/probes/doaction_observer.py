"""Source-bound block-entry instrumentation, not statement/call coverage."""
import hashlib
import json
import re

FRAME_ACTION = re.compile(r'(?:DefineSprite_(\d+)/)?frame_(\d+)/DoAction.as')


def inventory(bundle):
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
        record['id'] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        records.append(record)
    return records


def instrument(source, record):
    if not record['instrumented']:
        return source
    # Only entry into the authored block is observed. Function declarations
    # and untaken branches must not be counted as calls executed.
    return ('_root.aiEvent("doaction_entry", "' + record['id'] + '," + escape(String(this)) + "," + _currentframe);\n' + source)
