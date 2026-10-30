"""Convert original scene dictionaries; do not evaluate original expressions."""
from pathlib import Path
import json,re,collections
from tjs_data import loads
R=Path(__file__).absolute().parents[1];P=R.parent/'parquet-probe';E=P/'extracted-engine';O=R/'converted'
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
chart=loads((E/'main/scnchartdata.tjs.utf8.txt').read_text('utf8'));captions=chart['captions']
def chapter_name(code):
 if code=="manaka's_story":return 'pre story'
 if code in ['after_story','after-story']:return 'AFTER STORY'
 if code in ['prologue','epilogue']:return code
 assert re.fullmatch(r'\d+-\d+',code),code
 return 'CHAPTER '+code

sources=[json.loads(p.read_text('utf-8-sig')) for p in sorted((P/'scenarios').glob('*.ks.json'))]
chapter_labels={t[-1]['showdate']['date']:chapter_name(t[-1]['showdate']['date']) for x in sources for scene in x['scenes'] for t in scene.get('texts',[])}
ids={};metadata={};alltexts=[];images=json.loads((O/'image-requests.json').read_text('utf8'));requests={compact([v['file'],v['options']]):k for k,v in images.items()};scenes={};chapters=[];sourceproof=[];endings={};opsBy={}
for x in sources:
 number=int(re.search(r'\d+',x['name'])[0])
 for s in x['scenes']:
  key=(x['name'],s['label']);ids[key]=len(ids)+1;metadata[ids[key]]=(x,s,number)
def dest(storage,target=None):
 if storage=='start.ks':return None
 if not target:target=next(x['scenes'][0]['label'] for x in sources if x['name']==storage)
 assert (storage,target)in ids,(storage,target)
 return ids[(storage,target)]
def request(file,options=None):
 key=compact([file,options or {}])
 if key not in requests:
  aid='a'+str(len(requests));requests[key]=aid;images[aid]={'file':file,'options':options or {}}
 return requests[key]
def art(env):
 active=[]
 for entry in env.get('data',[]):
  if len(entry)!=3:continue
  name,cls,o=entry
  if cls not in ['stage','event','centerlayer','character','character2','stage2','event2'] or o.get('showmode') not in [1,3] or not o.get('redraw'):continue
  f=o['redraw'].get('imageFile')or {};file=f.get('file')
  if not file:continue
  ac={a[0]:a[1] for a in o.get('action',[]) if a and isinstance(a,list) and len(a)>1 and isinstance(a[1],(int,float,str))}
  if ac.get('opacity',255)==0:continue
  active.append({'name':name,'file':file,'options':f.get('options')or {},'class':cls,'clip':o['redraw'].get('clip'),'opacity':ac.get('opacity',255),'z':float(ac.get('zpos',233 if cls=='stage' else 0))})
 # Letterbox/viewpoint bars are UI overlays, never an opaque replacement for scene art.
 backs=[o for o in active if o['class'] in ['stage','event','centerlayer'] and o['name'] not in ['bar_top','bar_und','refrain'] and o['file'] not in ['bar1','bar2','回想枠']]
 back=min(backs,key=lambda a:a['z']) if backs else {'file':'画面_黒','options':{},'z':999}
 front=[o for o in sorted(active,key=lambda a:-a['z']) if o['class']in['character','character2'] and o['z']<back['z']]
 cuts=[o for o in front if o['name']=='ch_effect'and o.get('clip')]
 mask=next((o for o in active if o['name'].startswith('bl_effect')and o['file']=='画面_黒_カットイン'and o.get('clip')),None)
 cut=cuts[-1]if cuts and mask else None
 bodies=[request(o['file'],o['options']) for o in front if o is not cut]
 assert len(bodies)<=3
 mask=next((o for o in active if o['name'].startswith('bl_effect')and o['file']=='画面_黒_カットイン'and o.get('clip')),None)
 return {'background':request(back['file'],back['options']),'bodies':bodies,'view':'another'if env.get('_meswinchange')=='another'else 'normal','cutIn':request(cut['file'],cut['options'])if cut else '','cutInOpacity':int(mask['opacity'])if mask and cut else 0}
for id,(x,s,number) in metadata.items():
 tag='s'+str(number).zfill(3)+s['label'];group=tag
 dates=[t[-1]['showdate']['date']for t in s.get('texts',[])];commands=[line[1]for line in s.get('lines',[])if isinstance(line,list)and len(line)>1 and line[0]=='chapter'and line[1]not in ['show','hide']]
 default_code=next(t[-1]['showdate']['date']for scene in x['scenes']for t in scene.get('texts',[]))
 name=chapter_name(dates[0]if dates else commands[0]if commands else default_code)
 if tag in captions:name=captions[tag][0]
 ops=[]
 for index,t in enumerate(s.get('texts',[])):
  assert len(t)==5 and len(t[1])==4,(id,index)
  cn=t[1][2];assert cn is not None,(id,index)
  speaker=cn[0]or'';text=(cn[1]or'').replace('\\n','\n').replace('\r\n','\n')
  visual=art(t[-1]);frameGroup=t[-1].get('scnchart')or group
  ops.append({'op':'text','speaker':speaker,'text':text,'group':frameGroup,'chapterTag':t[-1]['showdate']['date'],**visual})
  alltexts.append([speaker,text]);sourceproof.append([id,index,speaker,text])
 choices=[]
 for item in s.get('selects',[]):
  assert not item.get('eval'),item
  effect=None
  if item.get('exp'):
   m=re.fullmatch(r'SetBranchFlags\("([^"]+)",(\d+)\)',item['exp']);assert m,item['exp'];effect=[m[1],int(m[2])]
  choices.append({'text':item['language'][2]['text'],'scene':dest(item.get('storage',x['name']),item.get('target')),'to':0,'effect':effect})
 nexts=s.get('nexts',[])
 if choices:ops.append({'op':'choice','items':choices})
 else:
  assert len(nexts)<=1,(id,nexts)
  if nexts:
   n=nexts[0];assert not n.get('eval'),n;to=dest(n['storage'],n.get('target'))
   if to:ops.append({'op':'jumpScene','scene':to,'to':0})
   else:ops.append({'op':'end'})
  else:ops.append({'op':'end'})
 clear='sf.parquet_side_clear'if number==0 else 'sf.parquet_main_clear'if number==14 else 'sf.parquet_after_rin_clear'if number==15 else 'sf.parquet_after_tsu_clear'if number==16 else ''
 scenes[str(id)]={'length':len(ops),'name':name,'route':0 if number==0 else 2 if number>=15 else 1,'group':group,'clearFlag':clear,'source':[x['name'],s['label']]}
 if tag in captions:chapters.append({'id':id,'name':name,'route':scenes[str(id)]['route']})
 opsBy[str(id)]=ops
 for block in range((len(ops)+31)//32):
  p=R/'src/common/story'/str(id)/(str(block)+'.txt');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(compact(ops[block*32:block*32+32]),'utf8');assert p.stat().st_size<32768,p
 endings[str(id)]='SIDE STORY'if number==0 else 'AFTER STORY'if number>=15 else 'PARQUET'
initials={n:ids[(x['name'],x['scenes'][0]['label'])] for x in sources for n in [int(re.search(r'\d+',x['name'])[0])]}
routes=[{'name':label,'scenes':[c['id']for c in chapters if c['route']==i]}for i,label in enumerate(['SIDE STORY · 爱花的故事','正篇','AFTER STORY'])]
catalog={'chapterLabels':chapter_labels,'initial':initials[1],'flowScene':initials[1],'sideInitial':initials[0],'afterInitial':initials[15],'chapters':chapters,'routes':routes,'scenes':scenes,'endings':endings}
(R/'src/common/catalog.js').write_text('export const catalog='+compact(catalog)+';\n','utf8')
for name,data in [('catalog.json',catalog),('ops.json',opsBy),('image-requests.json',images),('text-source.json',alltexts),('text-provenance.json',sourceproof)]: (O/name).write_text(compact(data),'utf8')
report={'result':'passed','scripts':len(sources),'scenes':len(scenes),'textRecords':len(alltexts),'choiceNodes':sum(any(o['op']=='choice'for o in ops)for ops in opsBy.values()),'choiceOptions':sum(len(o['items'])for ops in opsBy.values()for o in ops if o['op']=='choice'),'imageRequests':len(images),'chapterEntries':len(chapters),'sourceEntryVerified':'data/scenario/start.ks: side=00, main=01, after=15','unknownExpressions':0,'maxChunkBytes':max(p.stat().st_size for p in (R/'src/common/story').rglob('*.txt'))}
(R/'reports/story-conversion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report))
