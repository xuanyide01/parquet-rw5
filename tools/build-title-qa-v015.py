"""Build an independent endpoint-fixture QA app; never patch the production app."""
from pathlib import Path
import json,subprocess,shutil,os
R=Path(__file__).resolve().parents[1];Q=R.parent/'parquet-title015-qa';assert Q.resolve().is_relative_to(R.parent.resolve());Q.mkdir(exist_ok=True)
D=R/'reports/native-v015';D.mkdir(exist_ok=True)
node="const fs=require('fs'),{api}=require('./tests/fixture.cjs');fs.writeFileSync('reports/native-v015/qa-slot-fixtures.json',JSON.stringify([103,107].map((id,i)=>({key:api.slotKey(i),save:api.createSave(api.newState(id,true),'play',0)}))));"
subprocess.run(['node','-e',node],cwd=R,check=True)
shutil.copytree(R/'src',Q/'src',dirs_exist_ok=True);(Q/'tools').mkdir(exist_ok=True);(Q/'reports').mkdir(exist_ok=True)
for name in ['build.cjs','repack-rpk.cjs']:shutil.copyfile(R/'tools'/name,Q/'tools'/name)
p=Q/'src/manifest.json';m=json.loads(p.read_text('utf8'));m.update(package='com.codex.parquet.rw5.titleqa',name='PARQUET标题测试');p.write_text(json.dumps(m,ensure_ascii=False,indent=2),'utf8')
p=Q/'tools/build.cjs';p.write_text(p.read_text('utf8').replace('com.codex.parquet.rw5','com.codex.parquet.rw5.titleqa'),'utf8')
p=Q/'src/common/progress.js';s=p.read_text('utf8').replace('return {version:1,variables:{}}',"return {version:1,variables:{'sf.parquet_main_clear':true,'sf.parquet_side_clear':true}}",1);p.write_text(s,'utf8')
seed=''
for i,row in enumerate(json.loads((D/'qa-slot-fixtures.json').read_text('utf8'))):
 value=json.dumps(json.dumps(row['save'],ensure_ascii=False,separators=(',',':')),ensure_ascii=False)
 seed+="storage.set({key:"+json.dumps(row['key'])+",value:"+value+",success:()=>console.log('PARQUET_QA endpoint slot ready',"+str(i+1)+"),fail:()=>console.log('PARQUET_QA endpoint slot failed')});"
p=Q/'src/pages/index/index.ux';s=p.read_text('utf8').replace('this.readProgress();','this.readProgress();'+seed,1);p.write_text(s,'utf8');shutil.copyfile(R/'package.json',Q/'package.json')
for f in(Q/'src').rglob('*'):
 if f.suffix in ['.js','.ux']:f.write_text(f.read_text('utf8').replace('parquet_rw5_','parquet_titleqa_'),'utf8')
assert 'PARQUET_QA'not in(R/'src/pages/index/index.ux').read_text('utf8')
if not os.environ.get('WATCH_COMPAT_TOOLKIT'):os.environ['WATCH_COMPAT_TOOLKIT']=str(R.parent/'legacy-toolkit/node_modules/aiot-toolkit')
subprocess.run(['node','tools/build.cjs'],cwd=Q,check=True)
