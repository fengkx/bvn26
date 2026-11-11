"""Byte-level four-channel provenance; observations never certify a call/lifetime."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r24_target_parser', HERE.parent / 'native-fight-r23/analyze.py')
r23 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r23)


def tag_prefixes(run_id):
    return {'root': ('M002|' + run_id + '|').encode(),
            'side': ('M002SIDE|' + run_id + ',').encode(),
            'literal': ('M002LITERAL|' + run_id + '|').encode(),
            'target': ('M002TARGET|' + run_id + '|').encode()}


def reject_stale_prelaunch(prelaunch, prefixes):
    if any(prefix in prelaunch for prefix in prefixes.values()):
        raise ValueError('Run tag already present before launch')


def validate_channels(prelaunch, final, run_id):
    prefixes = tag_prefixes(run_id)
    reject_stale_prelaunch(prelaunch, prefixes)
    for name, prefix in prefixes.items():
        family = prefix.split(b'|', 1)[0] + b'|'
        if any(line.startswith(family) and not line.startswith(prefix) for line in final.splitlines()):
            raise ValueError('Foreign ' + name + ' tag')
    # Do not remove target records from combined order: they remain barriers to
    # inherited adjacency-based consumer/continuation classifiers.
    targets = r23.target_observations(final, run_id)
    counts = {name: sum(line.startswith(prefix) for line in final.splitlines())
              for name, prefix in prefixes.items()}
    return counts, targets


def validate_build(metadata):
    expected = {
        'game/main.swf': ['root/547:12', 'root/637:12',
                          'root/2012:39/sprite1813/1:12',
                          'root/2106:39/sprite1900/1:12',
                          'root/2198:39/sprite1991/1:12'],
        'game/fighter/yihu.swf': ['root/19:39/sprite16/1:12',
                                 'root/644:39/sprite638/308:12'],
    }
    if (metadata.get('facility') != 'r23'
            or metadata.get('target_site') != 'DefineSprite_638/frame_174/DoAction.as'
            or metadata.get('changed_tag_paths_by_asset') != expected
            or metadata.get('target_builder_sha256') != r23.sha(HERE.parent / 'native-fight-r23/build_observer.py')):
        raise ValueError('Receipt-matched r23 target build required')
