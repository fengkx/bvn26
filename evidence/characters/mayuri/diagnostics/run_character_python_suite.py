import hashlib,json,sys,time,unittest
from pathlib import Path
root=Path.cwd();tmp=Path('/private/tmp/bvn-mayuri-port')
paths=json.loads((tmp/'juugo-test-modules.json').read_text())
paths+=['tools/tests/test_mayuri_import.py','tools/tests/test_import_guards.py','tools/tests/test_controller_compound_assignment.py']
paths=sorted(set(paths));assert len(paths)==68
sys.path[:0]=[str(root/'tools/tests'),str(root)]
modules=[Path(p).stem for p in paths]
suite=unittest.TestLoader().loadTestsFromNames(modules)
start=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
report={'scope':'Current versions of the 65 PR #44 test modules, plus Mayuri, import guards and compound-assignment checks; not the unrelated historical-sampling test inventory.','inventory_revision':'875506cf','seconds':time.monotonic()-start,'tests_run':result.testsRun,'passed':result.wasSuccessful(),'failures':[(t.id(),s) for t,s in result.failures],'errors':[(t.id(),s) for t,s in result.errors],'skipped':[(t.id(),s) for t,s in result.skipped],'modules':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}}
(tmp/'character-python-suite.json').write_text(json.dumps(report,indent=2)+'\n')
sys.exit(0 if result.wasSuccessful() else 1)
