"""Render exact original layer selections; reuse bodies and small expression patches."""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageOps,ImageFont
import json,csv,hashlib,io,re,math,statistics
R=Path(__file__).absolute().parents[1];P=R.parent/'parquet-probe';E=P/'extracted-engine';D=R/'src/common/images';D.mkdir(exist_ok=True)
compact=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'))
requests=json.loads((R/'converted/image-requests.json').read_text('utf8'));plans=json.loads((R/'reports/portrait-plan.json').read_text('utf8'))
pngs={p.stem.lower():p for folder in ['data','bgimage','evimage']for p in(E/folder).rglob('*')if p.suffix.lower()=='.png'}
env=(E/'main/envinit.tjs.utf8.txt').read_text('utf8')
alternatives={a.lower():b.lower() for a,b in re.findall(r'"([^"]+)"\s*,[^\n]+?altStorage:"([^"]+)"',env,re.I)}
diffs={}
for row in csv.reader((E/'main/imagediffmap.csv.utf8.txt').read_text('utf8').splitlines()):
 if len(row)>=4:diffs[row[0].strip().lower()]=[v.strip()for v in row[1:4]]
existing={compact([v['file'],v['options']]):k for k,v in requests.items()};gallery=[]
def add(file):
 key=compact([file,{}])
 if key not in existing:existing[key]='a'+str(len(requests));requests[existing[key]]={'file':file,'options':{}}
 return existing[key]
for row in csv.reader((E/'main/cglist.csv.utf8.txt').read_text('utf8').splitlines()):
 if not row or not row[0].lower().startswith('thum_'):continue
 group=row[0][5:].upper()
 for entry in row[1:]:
  if not entry.strip():continue
  for i,file in enumerate(entry.strip().split('|')):
   if i:file=file.lstrip('*')
   if file.lower()not in diffs and file.lower()not in pngs and file.lower()not in alternatives:
    if i:continue
    raise ValueError('Missing gallery entry '+file)
   aid=add(file)
   if not any(x['group']==group and x['image']==aid for x in gallery):gallery.append({'group':group,'image':aid,'label':group,'source':file})
pimgcache={};layercache={};bodycache={};hashes={};mapping={};failures=[];count=0

def opened(path):
 key=str(path)
 if key not in layercache:
  if len(layercache)>55:layercache.clear()
  layercache[key]=Image.open(path).convert('RGBA')
 return layercache[key]
def layerfile(l):return P/'decoded-layers'/Path(l['id']).with_suffix('.png')
def blend(c,im,xy,kind=13,opacity=255):
 if opacity!=255:im=im.copy();im.putalpha(im.getchannel('A').point(lambda a:a*opacity//255))
 assert kind in [13,16],kind
 if kind==16:
  x,y=xy;under=c.crop((x,y,x+im.width,y+im.height));b=ImageChops.overlay(under.convert('RGB'),im.convert('RGB')).convert('RGBA');b.putalpha(im.getchannel('A'));c.alpha_composite(b,xy)
 else:c.alpha_composite(im,xy)
def store(im,kind='PNG'):
 global count
 if kind=='JPEG':
  rgb=Image.new('RGB',im.size,'white');rgb.paste(im,mask=im.getchannel('A')if im.mode=='RGBA'else None);im=rgb
 else:im=im.quantize(colors=192,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
 out=io.BytesIO();im.save(out,format=kind,optimize=True,**({'quality':66,'subsampling':2}if kind=='JPEG'else{}));raw=out.getvalue();h=hashlib.sha256(raw).hexdigest()
 if h not in hashes:
  rel=str(count//64).zfill(2)+'/'+str(count%64).zfill(2)+('.jpg'if kind=='JPEG'else'.png');count+=1;(D/Path(rel).parent).mkdir(exist_ok=True);(D/rel).write_bytes(raw);hashes[h]='/common/images/'+rel
 return hashes[h]
# One face scale per original pose, shared by every expression and outfit.
face_samples={};seen_faces=set()
for plan in plans.values():
 faces=[l for l in plan['layers']if l['face']]
 signature=(plan['base'],tuple(l['id']for l in faces))
 if signature in seen_faces:continue
 seen_faces.add(signature)
 left=min(l['left']for l in faces);top=min(l['top']for l in faces);right=max(l['left']+l['width']for l in faces);bottom=max(l['top']+l['height']for l in faces)
 face_samples.setdefault(plan['base'],[]).append(((left+right)/2,(top+bottom)/2,bottom-top))
face_references={base:{'x':statistics.median(v[0]for v in samples),'y':statistics.median(v[1]for v in samples),'height':statistics.median(v[2]for v in samples)}for base,samples in face_samples.items()}
PORTRAIT_HEIGHT=262;SOURCE_SCALE=0.15;FACE_CENTER_Y=64

def portrait(aid):
 plan=plans[aid];nonface=[l for l in plan['layers']if not l['face']];faces=[l for l in plan['layers']if l['face']]
 key=compact([plan['base'],[l['id']for l in nonface]])
 if key not in bodycache:
  box=[min(l['left']for l in nonface),min(l['top']for l in nonface),max(l['left']+l['width']for l in nonface),max(l['top']+l['height']for l in nonface)]
  reference=face_references[plan['base']];scale=SOURCE_SCALE;box[1]=round(reference['y']-FACE_CENTER_Y/scale);box[3]=box[1]+round(PORTRAIT_HEIGHT/scale);c=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]))
  for l in nonface:blend(c,opened(layerfile(l)),(l['left']-box[0],l['top']-box[1]),l['type'],l['opacity'])
  scale=PORTRAIT_HEIGHT/c.height;w=max(1,round(c.width*scale));small=c.resize((w,PORTRAIT_HEIGHT),Image.Resampling.LANCZOS)
  bodycache[key]={'image':small,'src':store(small),'box':box,'scale':scale}
 b=bodycache[key];meta={'src':b['src'],'width':b['image'].width,'height':PORTRAIT_HEIGHT,'portrait':True,'source':plan['base'],'crop':b['box'],'faceAnchor':[round((face_references[plan['base']]['x']-b['box'][0])*b['scale'],3),FACE_CENTER_Y],'faceReferenceHeight':round(face_references[plan['base']]['height']*b['scale'],4),'sourceScale':round(b['scale'],7)}
 if faces:
  box=b['box'];scale=b['scale'];left=max(box[0],min(l['left']for l in faces));top=max(box[1],min(l['top']for l in faces));right=min(box[2],max(l['left']+l['width']for l in faces));bottom=min(box[3],max(l['top']+l['height']for l in faces))
  rect=[max(0,math.floor((left-box[0])*scale)),max(0,math.floor((top-box[1])*scale)),min(meta['width'],math.ceil((right-box[0])*scale)),min(PORTRAIT_HEIGHT,math.ceil((bottom-box[1])*scale))]
  left=box[0]+math.floor(rect[0]/scale);top=box[1]+math.floor(rect[1]/scale);right=box[0]+math.ceil(rect[2]/scale);bottom=box[1]+math.ceil(rect[3]/scale)
  patch=Image.new('RGBA',(right-left,bottom-top))
  for l in plan['layers']:
   if l['left']>=right or l['top']>=bottom or l['left']+l['width']<=left or l['top']+l['height']<=top:continue
   blend(patch,opened(layerfile(l)),(l['left']-left,l['top']-top),l['type'],l['opacity'])
  patch=patch.resize((rect[2]-rect[0],rect[3]-rect[1]),Image.Resampling.LANCZOS)
  meta.update(patch=store(patch),patchRect=[rect[0],rect[1],patch.width,patch.height])
 return meta

def static(file,options):
 name=file.lower().removesuffix('.png')
 if name in alternatives:name=alternatives[name]
 if name in pngs:return opened(pngs[name]).copy()
 if name in ['画面_黒','暗転','黒画面']:return Image.new('RGBA',(1920,1080),'black')
 if name in ['画面_白','白画面']:return Image.new('RGBA',(1920,1080),'white')
 if name in diffs:base,mode,selected=diffs[name];assert mode=='seton',(name,mode);names=selected.split(':')
 elif (P/'evimage-json'/(name+'.json')).exists():base=name;names=str(options.get('seton','Aa')).split(':')
 else:raise ValueError('Unknown original image '+name)
 if base not in pimgcache:pimgcache[base]=json.loads((P/'evimage-json'/(base+'.json')).read_text('utf-8-sig'))
 data=pimgcache[base];canvas=Image.new('RGBA',(data['width'],data['height']));byname={x['name'].lower():x for x in data['layers']if x.get('layer_type')==0 and x.get('layer_id',-1)>=0}
 for n in reversed(names):
  assert n.lower()in byname,(name,n)
  l=byname[n.lower()];lid=l.get('same_image',l['layer_id']);im=opened(P/'evimage-json'/base/(str(lid)+'.png'));blend(canvas,im,(l.get('left',0),l.get('top',0)),l.get('type',13),l.get('opacity',255))
 return canvas
for i,(aid,v) in enumerate(requests.items()):
 try:
  if v['file'].endswith('.stand'):mapping[aid]=portrait(aid)
  else:
   im=static(v['file'],v['options']);im.thumbnail((360,240),Image.Resampling.LANCZOS);mapping[aid]={'src':store(im,'JPEG'),'width':im.width,'height':im.height,'portrait':False,'source':v['file']}
 except Exception as e:failures.append({'id':aid,'original':v,'error':str(e)})
 if i%150==0:print('RENDERED',i,'files',count,flush=True)
(R/'converted/image-map.json').write_text(compact(mapping),'utf8');(R/'converted/image-requests.json').write_text(compact(requests),'utf8');(R/'reports/image-errors.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2),'utf8')
(R/'src/common/gallery.txt').write_text(compact(gallery),'utf8');(R/'src/common/assets.js').write_text('const assets='+compact({k:v['src']for k,v in mapping.items()})+';export function imagePath(id){return assets[id]||"";}\n','utf8')
(R/'reports/images.json').write_text(json.dumps({'requested':len(requests),'mapped':len(mapping),'uniqueFiles':count,'bytes':sum(p.stat().st_size for p in D.rglob('*')if p.is_file()),'bodyRecipes':len(bodycache),'portraitNormalization':{'bitmapHeight':PORTRAIT_HEIGHT,'sourceScale':SOURCE_SCALE,'localFaceCenterY':FACE_CENTER_Y,'method':'same source-pixel scale for every original 3750px canvas; median face anchors align heads; clothing width never changes scale'},'faceReferences':face_references,'galleryGroups':len(set(v['group']for v in gallery)),'galleryImages':len(gallery),'failures':failures},ensure_ascii=False,indent=2),'utf8')
print('IMAGE_REPORT',len(mapping),count,len(failures),sum(p.stat().st_size for p in D.rglob('*')if p.is_file()),flush=True)
assert not failures,failures[:6]
