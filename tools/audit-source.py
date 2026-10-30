from pathlib import Path
import json,re,collections
R=Path(__file__).resolve().parents[1];P=R.parent/'parquet-probe';E=P/'extracted-engine'
cat=json.loads((R/'converted/catalog.json').read_text('utf8'));ops=json.loads((R/'converted/ops.json').read_text('utf8'))
by={(v['source'][0],v['source'][1]):int(k)for k,v in cat['scenes'].items()}
sources=[json.loads(f.read_text('utf-8-sig'))for f in sorted((P/'scenarios').glob('*.ks.json'))]
entries={x['name']:by[(x['name'],x['scenes'][0]['label'])]for x in sources}
texts=choices=0;edges=0;ignoredMarker=0
for source in sources:
 for scene in source['scenes']:
  id=by[source['name'],scene['label']];a=ops[str(id)]
  original=[(t[1][2][0]or'',(t[1][2][1]or'').replace('\\n','\n').replace('\r\n','\n'))for t in scene.get('texts',[])]
  converted=[(t['speaker'],t['text'])for t in a if t['op']=='text'];assert original==converted,(id,source['name'])
  texts+=len(original);ignoredMarker+=sum(t.count('\ufffc')for _,t in original)
  expected=[]
  for s in scene.get('selects',[]):
   assert not s.get('eval');dest=s.get('storage',source['name']);destid=by[dest,s['target']]if s.get('target')else entries[dest]
   effect=None
   if s.get('exp'):
    match=re.fullmatch(r'SetBranchFlags\("([^"]+)",(\d+)\)',s['exp']);assert match,s['exp'];effect=[match[1],int(match[2])]
   expected.append({'text':s['language'][2]['text'],'scene':destid,'to':0,'effect':effect})
  if expected:assert a[-1]=={'op':'choice','items':expected};choices+=1
  else:
   nxt=scene.get('nexts',[]);assert len(nxt)<=1
   if not nxt or nxt[0]['storage']=='start.ks':assert a[-1]['op']=='end'
   else:
    n=nxt[0];assert not n.get('eval');destid=by[n['storage'],n['target']]if n.get('target')else entries[n['storage']]
    assert a[-1]=={'op':'jumpScene','scene':destid,'to':0};edges+=1
assert texts==11098 and choices==2
report={'result':'passed','originalScripts':len(sources),'originalScenes':len(by),'originalChineseTextRecordsMatched':texts,'choiceNodesAndAllDestinationsMatched':choices,'sceneEdgesMatched':edges,'unknownConditionalSuccessors':0,'nonprintingObjectMarkersPreservedInSourceHiddenInRenderer':ignoredMarker,'validationScope':'Independent comparison against engine-exported original SCN objects; static graph/control-flow equivalence, not a human full reading'}
(R/'reports/source-equivalence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(report)
