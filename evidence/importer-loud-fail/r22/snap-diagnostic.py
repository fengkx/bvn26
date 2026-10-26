from pathlib import Path
import argparse
import json,math,gzip
parser = argparse.ArgumentParser(description="Rejected diagnostic: snap only Godot normalization; keep pinned native unchanged")
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
out=args.output.resolve()
for source in Path('evidence/importer-loud-fail/r03/components/components').iterdir():
 if not source.is_dir():continue
 dest=out/'components'/source.name;dest.mkdir(parents=True,exist_ok=True)
 rows=json.loads((source/'cases.json').read_text())
 for row in rows:
  n=row['normalization'];n['x']=math.floor(n['x']*20)/20;n['y']=math.floor(n['y']*20)/20;n['scale']=math.floor(n['scale']*65536)/65536
 (dest/'cases.json').write_text(json.dumps(rows))
 (dest/'native.log').write_bytes(gzip.decompress((source/'native.log.gz').read_bytes()))
