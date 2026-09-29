"""Prepare the fixed confirmation batch; run from dtr-stability root."""
import hashlib, json, os, platform, shutil, subprocess, sys
from pathlib import Path
EXPECTED = {'run_protocol.py': '906380a8f12faa4ef0f2f37a461e5d5661b0159062d621efedef7b8589abbc98', 'harness.py': 'a2280cfa8a1a7d282efa22f16de99932e1febedf4e240adcfcc8540ee6fd39c7'}
root=Path.cwd(); package=Path(__file__).resolve().parent
for name, expected in EXPECTED.items():
    path=root/name
    if not path.exists() or hashlib.sha256(path.read_text().encode()).hexdigest()!=expected:
        raise SystemExit('STOP: '+name+' differs from the inspected upload. Share the current file before proceeding.')
sim=Path(os.environ.get('DTR_SIMRD',''))
if not (sim/'simrd').is_dir(): raise SystemExit('Set DTR_SIMRD to external/simrd first.')
import networkx
out=root/'results/protocol/confirmation_20260929'
def git(args,cwd):
    cp=subprocess.run(['git',*args],cwd=cwd,capture_output=True,text=True)
    return {'returncode':cp.returncode,'stdout':cp.stdout.strip(),'stderr':cp.stderr.strip()}
current={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in root.glob('*.py')}
if (out/'manifest.json').exists():
    old=json.loads((out/'manifest.json').read_text())
    if old['source_sha256']!=current: raise SystemExit('STOP: local Python sources changed since batch preparation.')
    for name in ['PLAN.md','points.jsonl']:
        if (out/name).read_bytes()!=(package/name).read_bytes(): raise SystemExit('STOP: confirmation plan changed.')
    print('Existing batch verified; resume without overwriting results.')
else:
    out.mkdir(parents=True,exist_ok=True)
    if (out/'results.jsonl').exists(): raise SystemExit('STOP: results exist without a manifest.')
    (out/'source_snapshot').mkdir(exist_ok=True)
    for f in root.glob('*.py'): shutil.copy2(f,out/'source_snapshot'/f.name)
    for name in ['PLAN.md','points.jsonl']: shutil.copy2(package/name,out/name)
    manifest={'source_sha256':current,'host':platform.node(),'platform':platform.platform(),
        'python':sys.version,'executable':sys.executable,'networkx':networkx.__version__,
        'repo_commit':git(['rev-parse','HEAD'],root),'repo_status':git(['status','--short'],root),
        'simulator_commit':git(['rev-parse','HEAD'],sim),'simulator_status':git(['status','--short'],sim)}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Plan, 52 points and provenance saved before execution.')
