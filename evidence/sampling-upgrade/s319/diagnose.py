"""Audit archived ones observer dependencies; do not infer a live entry clock."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '4e486b4d9c0764d1abba983c3af8ae4d1bcf6a48'
ARCHIVE = 'evidence/sampling-upgrade/s274/native-build.tar.gz'
ROOT_MEMBER = 's274-patches/frame_1/DoAction.as'
ENTRY_MEMBER = 's274-patches/DefineSprite_1810/frame_1/DoAction.as'
LIFE_PREFIX = 's274-patches/DefineSprite_1813/frame_1/PlaceObject2_1810_3/'
GATES = {
    'observer': 'S319_ENTRY_INSTANCE_RESOLVER_UNPROVED',
    'independent-controls': 'S319_INDEPENDENT_CONTROLS_UNPROVED',
    'child-clock': 'S319_CHILD_CLOCK_UNPROVED',
    'fresh-capture': 'S319_FRESH_CAPTURE_BLOCKED',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_prior():
    spec = importlib.util.spec_from_file_location('s319_locked_s310', HERE.parent / 's310/diagnose.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_sources():
    names = [ROOT_MEMBER, ENTRY_MEMBER] + [
        LIFE_PREFIX + 'CLIPACTIONRECORD onClipEvent(' + phase + ').as'
        for phase in ('load', 'unload')]
    with tarfile.open(ROOT / ARCHIVE) as archive:
        return {name: archive.extractfile(name).read().decode() for name in names}


def channel_audit(sources):
    """Bound exact archived source, not a general AS parser or runtime resolver."""
    root = sources[ROOT_MEMBER]
    lines = root.splitlines()
    expected = [
        '_root.s274Generation = 0;',
        '_root.s274Life = function(mc, phase)',
        '{',
        '   if(phase == "load") { mc.s274Generation = ++_root.s274Generation; }',
        '   if(phase == "unload" && mc.s274Generation == 2) _root.s274Unloaded2 = true;',
        '   _root.aiEvent("s274_life", phase + "," + String(mc) + "," + mc.getDepth() + "," + mc.s274Generation + "," + mc._currentframe);',
        '};',
        '_root.s274Entry = function(mc)',
        '{',
        '   if(mc.s274Generation == 2 && _root.aiFight == 1) _root.s274RetainedEntry2 = true;',
        '   _root.aiEvent("s274_entry", String(mc) + "," + mc.getDepth() + "," + mc.s274Generation + "," + mc._currentframe);',
        '};',
        '_root.s274State = function(phase, mc)',
        '{',
        '   _root.aiEvent("s274_state", phase + "," + String(mc) + "," + mc.getDepth() + "," + mc.s274Generation + "," + mc._currentframe);',
        '};',
    ]
    if lines[:16] != expected:
        raise ValueError('archived observer source changed')
    if sources[ENTRY_MEMBER] != '_root.s274Entry(this);\n_root.s262Init(this,1810);\nstop();\n':
        raise ValueError('entry hook source changed')
    for phase in ('load', 'unload'):
        member = LIFE_PREFIX + 'CLIPACTIONRECORD onClipEvent(' + phase + ').as'
        if sources[member] != 'onClipEvent(' + phase + ') { _root.s274Life(this,"' + phase + '"); }\n':
            raise ValueError('lifecycle hook source changed')
    sections = [('generation_seed', 1, 1), ('life', 2, 7),
                ('entry', 8, 12), ('state', 13, 16)]
    return {
        'archive': ARCHIVE,
        'members': {name: {'sha256': sha(text.encode()), 'line_count': len(text.splitlines())}
                    for name, text in sources.items()},
        'root_sections': [dict(role=role, member=ROOT_MEMBER, lines=[first, last],
                               source='\n'.join(lines[first - 1:last]))
                          for role, first, last in sections],
        'hooks': [{'member': name, 'source': text} for name, text in sources.items()
                  if name != ROOT_MEMBER],
        'serialized_operands': ['String(mc)', 'mc.getDepth()', 'mc.s274Generation', 'mc._currentframe'],
        'shared_sink': '_root.aiEvent',
        'sink_call_lines': [6, 11, 15],
        'generation_write_line': 4,
        'calibration_write_lines': [5, 10],
        'entry_hook_lexical_order': ['s274Entry(this)', 's262Init(this,1810)', 'stop()'],
        'independent_live_channel': None,
        'observer_off_surviving_channel': None,
        'interpretation': 'All three audited helper reports read the supplied mc and call the same AS sink. Generation is written by the load helper; calibration flags are written by life/entry helpers. This source dependency is not native allocation identity or action-preservation proof. Removing the sole audited sink leaves no independent witness in these reports; actual off/on behavior was not observed.',
        'audit_boundary': 'Four archived source members only. Lexical order is not dispatch order; no claim that independent facilities elsewhere are impossible or absent.',
    }


def diagnose():
    for name, digest in json.loads((HERE / 'input-sha256.json').read_text()).items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError('locked input changed: ' + name)
    historical = load_prior().diagnose()
    if historical != json.loads((HERE.parent / 's310/diagnosis.json').read_text()):
        raise ValueError('locked s310 diagnosis changed')
    return {
        'slice': 's319', 'base': BASE,
        'scope': 'AFTER-s317 rank #2 only: Independent ones entry clock',
        'production_admitted': False, 'native_parity_proven': False, 'm0_02_status': 'pending',
        'locked_s310_reproduced': True,
        'historical_validation_only': historical['historical'],
        'observer_dependency_audit': channel_audit(read_sources()),
        'qualification_matrix': historical['qualification_matrix'],
        'live_entry_resolver': None, 'live_instance_resolver': None,
        'observer_qualified': False, 'independent_controls_proved': False,
        'independent_child_clock_proved': False, 'fresh_capture_eligible': False,
        'new_builds': 0, 'new_player_launches': 0, 'new_captures': 0, 'new_images': 0,
        'other_ranks_executed': [], 'product_obligations_closed': 0,
        'blocker': 'The retained entry/life/state reporters share mc-derived operands and aiEvent. No independent live outer-instance lifetime and all-ten-frame entry channel is bound. Isolated repeated/changed/replacement/off-on controls remain unproved; fresh ones-only capture is blocked before launch.',
        'next_required_observation': 'Bind independent live outer-instance generation and target-entry dispatch for frames1-10, including actionless frames. Qualify isolated repeated/changed-target, replacement and observer-off/on trials with selection, entry and following root/callback boundary in the same run and lifetime before one fresh capture.',
        'exclusions': ['static glyph-as-entry', 'synthetic clock', 'empty-frame actions treated as neutral',
                       'scene/intro repair', 'cross-run images or tape', 'HUD reset',
                       's254-s318 edits', 'runtime/contracts/shared sampler/threshold/validator changes',
                       'rank 1 or ranks 3+ execution'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    for flag in GATES:
        parser.add_argument('--require-' + flag, action='store_true')
    args = parser.parse_args()
    result = diagnose()
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    failures = [code for flag, code in GATES.items()
                if getattr(args, 'require_' + flag.replace('-', '_'))]
    if failures:
        print('; '.join(failures) + ': ' + result['blocker'])
        return 1
    print('S319_DIAGNOSIS_OK production_admitted=false native_parity_proven=false')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
