import ast
import unittest
from pathlib import Path
from tools.probes.probe_owned_source_call import CALLEE, ENTRY, ENTRY_BYTES, SETUP_BYTES, RUNTIME, script_for_edges, capture_accepted


class SourceCallTests(unittest.TestCase):
    def edge(self):
        return {'site':hex(ENTRY),'target':hex(CALLEE),'bytes':ENTRY_BYTES[:10],
                'return_pc':hex(ENTRY+5)}

    def test_incomplete_native_capture_cannot_pass(self):
        result={'capture_complete':False,'owned_processes_remaining':[],
                'debugger_exit':0,'debugger_timed_out':False,
                'debugger':{'hardware_callsite_verified':True,'detached':True,'breakpoint_id':1,
                            'breakpoint_cleanup':[{'id':1,'removed':True}]}}
        self.assertFalse(capture_accepted(result))
        result['capture_complete']=True
        self.assertTrue(capture_accepted(result))
        result['debugger']['breakpoint_cleanup'][0]['removed']=False
        self.assertFalse(capture_accepted(result))

    def test_predeclared_site_is_unique_and_bytes_pinned(self):
        script = script_for_edges([self.edge()])(123,Path('/owned/player'),Path('/fresh/result'))
        ast.parse(script)
        self.assertEqual(len(bytes.fromhex(ENTRY_BYTES)),16)
        self.assertEqual(len(bytes.fromhex(SETUP_BYTES)),14)
        for edges in ([],[self.edge(),self.edge()],[dict(self.edge(),bytes='e800000000')]):
            with self.assertRaises(ValueError):script_for_edges(edges)

    def test_precall_abi_has_no_fabricated_stack_return(self):
        self.assertNotIn("regs['rsp']",RUNTIME)
        self.assertNotIn('return_load',RUNTIME)
        self.assertIn("'precall_stack_return_read'] = False",RUNTIME)
        self.assertIn("regs['rdi'] == regs['rbx']+0x48",RUNTIME)
        self.assertIn("regs['rsi'] == regs['r14']",RUNTIME)
        self.assertIn("regs['rdx'] == regs['rbp']-0x230",RUNTIME)
        self.assertLess(RUNTIME.index('if not all(relations.values())'),RUNTIME.index("result['input_matrix_bytes']"))

    def test_mismatched_setup_stops_before_operand_reads(self):
        tree = ast.parse(RUNTIME)
        body = next(node.body for node in tree.body if isinstance(node,ast.Try))
        start = next(i for i,node in enumerate(body) if isinstance(node,ast.Assign)
                     and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='relations')
        stop = next(i for i,node in enumerate(body) if isinstance(node,ast.Assign)
                    and isinstance(node.targets[0],ast.Subscript)
                    and isinstance(node.targets[0].slice,ast.Constant)
                    and node.targets[0].slice.value=='input_matrix_bytes')
        block = compile(ast.Module(body=body[start:stop+1],type_ignores=[]),'abi','exec')
        for field in ('rdi','rsi','rdx'):
            regs={'rbx':0x1000,'rdi':0x1048,'r14':0x2000,'rsi':0x2000,'rbp':0x4000,'rdx':0x3dd0}
            regs[field]+=1
            reads=[]
            namespace={'regs':regs,'result':{},'EDGE':self.edge(),
                       'read':lambda *args:reads.append(args) or bytes(28)}
            with self.assertRaises(RuntimeError):exec(block,namespace)
            self.assertEqual(reads,[])

    def test_independent_byte_obligation_remains_unmet(self):
        self.assertIn("'guest_virtual_entry_bytes_independently_verified': False",RUNTIME)
        self.assertIn("'physical_entry_bytes_independently_verified': False",RUNTIME)
        self.assertNotIn('read_guest_entry(',RUNTIME)
        self.assertIn('breakpoint set --hardware --address ',RUNTIME)
        self.assertIn('process.GetStopID() != prior_stop',RUNTIME)
        self.assertIn('target.BreakpointDelete(breakpoint_id)',RUNTIME)
        self.assertIn('process.Detach()',RUNTIME)
        self.assertNotIn('EvaluateExpression',RUNTIME)
