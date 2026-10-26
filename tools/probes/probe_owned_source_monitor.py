"""Add post-detach observation to the unchanged single source-call diagnostic."""
import argparse
import ast
import json
from pathlib import Path
from tools.probes.audit_affine_static_callers import analyze
from tools.probes.capture_native_player import player_binary
from tools.probes.monitor_owned_native import monitor_owned
from tools.probes.probe_owned_debugger import probe
from tools.probes.probe_owned_source_call import script_for_edges, capture_accepted


def timed_factory(factory):
    def generate(pid,binary,result_path):
        tree=ast.parse(factory(pid,binary,result_path))
        class DetachTiming(ast.NodeTransformer):
            count=0
            def visit_Assign(self,node):
                if (isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
                    and isinstance(node.value.func.value,ast.Name)
                    and node.value.func.value.id=='process' and node.value.func.attr=='Detach'):
                    self.count+=1
                    before=ast.parse("result['detach_call_start_monotonic']=time.monotonic()").body[0]
                    after=ast.parse("result['detach_call_end_monotonic']=time.monotonic()").body[0]
                    return [before,node,after]
                return node
        transform=DetachTiming();tree=transform.visit(tree)
        if transform.count != 1:
            raise ValueError('Expected exactly one unchanged detach call to instrument')
        return ast.unparse(ast.fix_missing_locations(tree))+'\n'
    return generate


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('build','output','player-app','disassembly'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--allow-window-activation',action='store_true');args=parser.parse_args()
    if not args.allow_window_activation:parser.error('Explicit native window activation authorization required')
    static=analyze(player_binary(args.player_app),args.disassembly,{})
    result=probe(args.build,args.output,args.player_app,45,
                 script_factory=timed_factory(script_for_edges(static['direct_edges'])),
                 explicit_breakpoints_requested=True,post_debugger=monitor_owned)
    (args.output/'static-callers.json').write_text(json.dumps(static,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not capture_accepted(result):raise SystemExit(1)
