from pathlib import Path
import json,csv,collections,unicodedata
from tjs_data import loads
R=Path(__file__).absolute().parents[1];P=R.parent/'parquet-probe';FG=P/'extracted-engine/fgimage'
req=json.loads((R/'converted/image-requests.json').read_text('utf8'));cache={};plans={};needed={};errors=[]
N=lambda x:unicodedata.normalize('NFKC',str(x))
def table(base):
 if base in cache:return cache[base]
 sinfo=next(FG.rglob(base+'.sinfo.utf8.txt'));pbd=next(FG.rglob(base+'.pbd.json'));records=json.loads(pbd.read_text('utf8'));byid={x['layer_id']:x for x in records[1:]}
 def path(x):
  p=byid.get(x.get('group_layer_id'));return (path(p)+'/'if p else'')+N(x['name'].replace('/','_'))
 bypath={path(x):x for x in records[1:] if x['layer_type']==0};dress=collections.defaultdict(list);face=collections.defaultdict(list)
 for row in csv.reader(sinfo.read_text('utf8').splitlines(),delimiter='\t'):
  if len(row)>=5 and row[0]=='dress':dress[(row[1],row[2],row[3])].append(N(row[4]))
  elif len(row)>=4 and row[0]=='face':face[row[1]].append(N(row[3]))
 cache[base]={'pbd':pbd,'records':records,'bypath':bypath,'dress':dress,'face':face};return cache[base]
for aid,v in req.items():
 if not v['file'].endswith('.stand'):continue
 try:
  stand=loads((FG/(v['file']+'.utf8.txt')).read_text('utf8'));op=v['options'];chosen=[]
  for item in stand:
   base=item['filename'];t=table(base);key=(str(op.get('dress','')),'diff',str(op.get('pose','1')))
   if key in t['dress']:chosen.append((base,t,key))
  assert len(chosen)==1,(v,len(chosen));base,t,key=chosen[0]
  paths=list(t['dress'][key])+list(t['dress'].get((key[0],'base',''),[]));face=t['face'].get(str(op.get('face','01')))
  assert face is not None,('Missing face',base,op)
  wanted=set(paths+face);layers=[]
  for path in wanted:
   if path not in t['bypath']:
    matches=[v for k,v in t['bypath'].items() if k.endswith('/'+path)]
    assert len(matches)==1,('Missing or ambiguous layer',base,path)
    t['bypath'][path]=matches[0]
   l=t['bypath'][path];source=t['pbd'].with_name(base+'_'+str(l['layer_id'])+'.tlg');assert source.exists(),source
   relative=source.relative_to(FG).as_posix();dest=P/'decoded-layers'/Path(relative).with_suffix('.png');dest.parent.mkdir(parents=True,exist_ok=True)
   needed[relative]={'input':str(source),'output':str(dest)}
   layers.append({**l,'id':relative,'face':path in face and path not in paths,'order':t['records'].index(l),'name':path})
  plans[aid]={'base':base,'canvas':[t['records'][0]['width'],t['records'][0]['height']],'layers':sorted(layers,key=lambda x:-x['order']),'original':v}
 except Exception as e:errors.append({'asset':aid,'request':v,'error':str(e)})
(R/'reports/portrait-plan.json').write_text(json.dumps(plans,ensure_ascii=False),'utf8')
(R/'reports/tlg-plan.json').write_text(json.dumps(list(needed.values()),ensure_ascii=False),'utf8')
(R/'reports/portrait-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'portraits':len(plans),'neededLayers':len(needed),'errors':len(errors),'examples':errors[:4]},ensure_ascii=True))
assert not errors
