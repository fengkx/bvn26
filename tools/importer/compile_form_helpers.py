"""Lower BODY-owned transformation helpers without admitting a form transaction.

The caller must supply consumers for every emitted effect. In particular a parent
nextFrame effect is not a body goto, and publishing these helpers does not make a
replacement profile usable by the frame compiler.
"""
import json
import re

NAMES = ('wankai', 'doWanKai', 'initCtrl', 'randAI')
KEYS = ('上', '下', '左', '右', '斩', '跳', '冲', '招', '必杀', '换')
ROOT_KEYS = ('w', 's', 'a', 'd', 'j', 'k', 'l', 'u', 'i', 'o',
             '上箭', '下箭', '左箭', '右箭', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6')
FIELDS = {'_parent.万解': 'transformed', '_parent.中转.hp': 'transfer_hp',
          '_parent.中转.ql': 'transfer_ql', '_parent._name': 'wrapper_name',
          '_root._y': 'root_y', '_root.AI': 'difficulty', **{'_root.' + k: 'key:' + k for k in ROOT_KEYS}}
CALLS = frozenset((*NAMES, 'form_read', 'form_write', 'form_effect', 'form_interval', 'form_clear_interval', 'form_random', 'form_next_frame', 'form_init_trace'))


def compile_helpers(functions, compile_function, *, random_sites):
    code = ''
    for name in NAMES:
        if name not in functions:
            raise ValueError('Missing BODY form helper: ' + name)
        params, body = functions[name]
        if params:
            raise ValueError('Unsupported BODY form helper parameters: ' + name)
        lines = []
        for raw in body.splitlines():
            indent = raw[:len(raw) - len(raw.lstrip())]
            line = raw.strip()
            if name == 'randAI' and (m := re.fullmatch(r'(attran|defran|goran|jumpran|bisharan) = Math\.random\(\) \* (_loc\d+_);', line)):
                line = 'form_write(' + json.dumps('body_field:' + m[1]) + ',form_random(' + json.dumps(random_sites[m[1]]) + ') * ' + m[2] + ');'
            elif line == 'clearInterval(_root.feiint);':
                line = 'form_clear_interval("feiint");'
            elif line == '_root.feiint = setInterval(feixue,1000);':
                line = 'form_interval("feiint","feixue",1000);'
            elif line == '_root.airanset = setInterval(randAI,500);':
                line = 'form_interval("airanset","randAI",500);'
            elif line == '_parent.nextFrame();':
                # Native replacement retires the executing old BODY function.
                lines.extend([indent + 'if(!form_next_frame())', indent + '{', indent + '   return undefined;', indent + '}'])
                continue
            elif line in ('_parent.updateGJL();',
                          '_root.game["p" + pn].updateGJL();',
                          'AImain.gotoAndStop(1);', 'AImain.gotoAndStop(2);',
                          'AImain.unloadMovie();'):
                line = 'form_effect(' + json.dumps(line[:-1]) + ');'
            elif line in ('trace("p1");', 'trace("p2");', 'trace("initCtrl: " + _parent.useAI);'):
                # Keep diagnostic delivery ordered, including its source value.
                argument = '"p1"' if line == 'trace("p1");' else '"p2"' if line == 'trace("p2");' else 'form_init_trace(_parent.useAI)'
                line = 'form_write("trace",' + argument + ');'
            elif m := re.fullmatch(r'_this\.(\w+) = (.+);', line):
                if m[1] not in KEYS:
                    raise ValueError('Unsupported form key binding: ' + line)
                line = 'form_write(' + json.dumps('body_key:' + m[1], ensure_ascii=False) + ',' + m[2] + ');'
            elif m := re.fullmatch(r'(_parent\.(?:万解|中转\.(?:hp|ql))|_root\._y) = (.+);', line):
                line = 'form_write(' + json.dumps(FIELDS[m[1]]) + ',' + m[2] + ');'
            for source, key in sorted(FIELDS.items(), key=lambda pair: -len(pair[0])):
                line = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"|(?<![\w.])' + re.escape(source) + r'(?!\w)',
                              lambda match: match[0] if match[0].startswith('"') else 'form_read(' + json.dumps(key) + ')', line)
            lines.append(indent + line)
        # These helpers retain the useAI==undefined guard and both AI/player
        # branches. They cannot use the ordinary CPU-only specialization.
        code += compile_function(name, params, '\n'.join(lines), CALLS, player=True)
    code += '''
func form_init_trace(v: Variant) -> String:
\tif v == null:
\t\treturn "initCtrl: undefined"
\tassert(v is bool, "Uncompiled useAI trace value")
\treturn "initCtrl: " + ("true" if v else "false")

func form_next_frame() -> Variant:
\treturn adapter.form_next_frame()

func form_random(site: String) -> Variant:
\treturn adapter.form_random(site)

func form_read(key: String) -> Variant:
\treturn adapter.form_read(key)

func form_write(key: String, v: Variant) -> Variant:
\tadapter.form_write(key, v)
\treturn null

func form_effect(operation: String) -> Variant:
\tadapter.form_effect(operation)
\treturn null

func form_interval(slot: String, method: String, delay: int) -> Variant:
\tadapter.form_interval(slot, Callable(self, method), delay)
\treturn null

func form_clear_interval(slot: String) -> Variant:
\tadapter.form_clear_interval(slot)
\treturn null
'''
    return code
