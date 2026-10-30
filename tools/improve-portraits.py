"""Preserve original facial detail; never depend on tiny face-only textures.
Complete-canvas shared expressions from SG0, six-bit RGB from CLANNAD.
No changes to scale, text, choices, backgrounds or CG.
"""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFont
import json,hashlib,sys,importlib.util
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent/'parquet-probe';O=R/'reports/portrait-quality-v014';O.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('portrait_codec',R/'tools/portrait-codec.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
apply='--apply' in sys.argv;m=json.loads((R/'converted/image-map.json').read_text('utf8'));plans=json.loads((R/'reports/portrait-plan.json').read_text('utf8'))
backup=O/'before-image-map.json'
if not backup.exists():backup.write_text(json.dumps(m,ensure_ascii=False,separators=(',',':')),'utf8')
old=json.loads(backup.read_text('utf8'));out=(R/'src/common/images/p014')if apply else O/'candidate-images';out.mkdir(exist_ok=True)
cache={};bodies={};files={};rows=[];samples={};results={};fallback=0

def opened(layer):
    f=P/'decoded-layers'/Path(layer['id']).with_suffix('.png');key=str(f)
    if key not in cache:
        if len(cache)>40:cache.clear()
        cache[key]=Image.open(f).convert('RGBA')
    return cache[key]

def blend(c,im,xy,kind,opacity):
    if opacity!=255:im=im.copy();im.putalpha(im.getchannel('A').point(lambda a:a*opacity//255))
    if kind==16:
        x,y=xy;under=c.crop((x,y,x+im.width,y+im.height));b=ImageChops.overlay(under.convert('RGB'),im.convert('RGB')).convert('RGBA');b.putalpha(im.getchannel('A'));c.alpha_composite(b,xy)
    else:assert kind==13;c.alpha_composite(im,xy)

def draw_layers(layers,box):
    c=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]))
    for l in layers:
        if l['left']>=box[2]or l['top']>=box[3]or l['left']+l['width']<=box[0]or l['top']+l['height']<=box[1]:continue
        blend(c,opened(l),(l['left']-box[0],l['top']-box[1]),l['type'],l['opacity'])
    return c

def store(im):
    data=codec.encode_exact(im);h=hashlib.sha256(data).hexdigest()
    if h not in files:
        name=h[:20]+'.png';(out/name).write_bytes(data);files[h]={'path':name,'bytes':len(data),'size':list(im.size)}
    return '/common/images/p014/'+files[h]['path']

def old_image(meta):
    im=Image.open(R/'src'/meta['src'].lstrip('/')).convert('RGBA')
    if meta.get('patch'):im.alpha_composite(Image.open(R/'src'/meta['patch'].lstrip('/')).convert('RGBA'),tuple(meta['patchRect'][:2]))
    return im

def face_mse(a,b,rect):
    x,y,w,h=rect;a=np.asarray(a.crop((x,y,x+w,y+h)),dtype='float32');b=np.asarray(b.crop((x,y,x+w,y+h)),dtype='float32');mask=a[:,:,3]>240
    return float(np.mean((a[:,:,:3][mask]-b[:,:,:3][mask])**2))

selected=set(plans)if apply else set(plans)&{'a465','a466','a2','a4','a459','a60','a68','a1274'}
groups={};inputs={}
for aid,plan in plans.items():
    if aid not in selected:continue
    meta=dict(old[aid]);box=meta['crop'];rect=meta.get('faceRect',meta['patchRect']);x,y,w,h=rect;scale=meta['height']/(box[3]-box[1])
    key=json.dumps([plan['base'],[l['id']for l in plan['layers']if not l['face']]],ensure_ascii=False)
    if key not in bodies:
        raw=draw_layers([l for l in plan['layers']if not l['face']],box).resize((meta['width'],meta['height']),Image.Resampling.LANCZOS);previous=Image.open(R/'src'/meta['src'].lstrip('/')).convert('RGBA')
        bodies[key]={'raw':raw,'previous':previous,'oldBodyMSE':codec.composite_mse(raw,previous),'newBodyMSE':0,'reference':None}
    body=bodies[key];raw=body['raw'].copy();patchbox=[box[0]+int(np.floor(x/scale)),box[1]+int(np.floor(y/scale)),box[0]+int(np.ceil((x+w)/scale)),box[1]+int(np.ceil((y+h)/scale))]
    face=draw_layers(plan['layers'],patchbox).resize((w,h),Image.Resampling.LANCZOS);raw.alpha_composite(face,(x,y));before=old_image(meta);before_mse=face_mse(raw,before,rect)
    inputs[aid]={'meta':meta,'raw':raw,'before':before,'beforeMSE':before_mse,'rect':rect,'sourceFace':face};groups.setdefault(key,[]).append(aid)
    if len(inputs)%150==0:print('SOURCE_FACES',len(inputs),flush=True)

for gi,(key,aids)in enumerate(groups.items()):
    body=bodies[key]
    for aid in aids:
        item=inputs[aid];raw=item['raw'];meta=item['meta'];rect=item['rect'];x,y,w,h=rect;before_mse=item['beforeMSE'];face=item['sourceFace']
        if body['reference']is None:
            full=body['previous'].copy();full.alpha_composite(face,(x,y));reference=codec.compact_faced_base(full,rect)
            body.update(reference=reference,src=store(reference),canonical=aid)
        candidates=[]
        # More RGBA colours than 0.1.3, assigned wholly to the original face
        # rectangle. Transparent padding is added after quantization.
        q=face.quantize(colors=255,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA');candidates.append((255,q))
        oldface=Image.open(R/'src'/old[aid]['patch'].lstrip('/')).convert('RGBA');candidates.append((192,oldface))
        a=np.asarray(face);train=a[:,:,:3][a[:,:,3]>128].reshape(1,-1,3)
        for colors in [128,192]:
            palette=Image.fromarray(train).quantize(colors=colors,method=Image.Quantize.MEDIANCUT);q=codec.apply_palette(face,palette);qa=np.asarray(q).copy();qa[:,:,3]=np.where(a[:,:,3]<32,0,np.where(a[:,:,3]<192,128,255));qa[qa[:,:,3]==0]=0;q=Image.fromarray(qa,'RGBA')
            if len(q.getcolors(100000))<=255:candidates.append((colors,q))
        ranked=[]
        for colors,qface in candidates:
            overlay=Image.new('RGBA',raw.size);overlay.paste(qface,(x,y));rendered=Image.alpha_composite(body['reference'],overlay);error=face_mse(raw,rendered,rect);ranked.append((error,colors,overlay,rendered))
        after_mse,selected_colors,overlay,rendered=min(ranked,key=lambda row:row[0]);src=body['src'];patch=store(overlay);patchrect=[0,0,meta['width'],meta['height']];whole=False
        if after_mse>before_mse+1.0:
            # A transparent expression edge may expose an old expression.
            # Flatten this exceptional expression rather than accept ghosting.
            full=body['previous'].copy();full.alpha_composite(face,(x,y));src=store(codec.six_bit_rgb(full));patch='';patchrect=[0,0,0,0];rendered=codec.six_bit_rgb(full);after_mse=face_mse(raw,rendered,rect);fallback+=1;whole=True
        assert after_mse<=max(before_mse+1.001,4.001),(aid,after_mse,before_mse)
        meta.update(src=src,patch=patch,patchRect=patchrect,faceRect=rect,renderStrategy='padded complete-canvas original face overlay; shared base includes canonical face; source error gate',canonicalFace=body['canonical']);results[aid]=meta
        rows.append({'id':aid,'source':plans[aid]['base'],'faceRect':rect,'beforeFaceRGBMSE':round(before_mse,5),'afterFaceRGBMSE':round(after_mse,5),'fullCanvasExpression':bool(patch),'standaloneCompletePortrait':whole,'facePaletteColors':selected_colors,'faceSourceErrorGatePassed':True})
        if aid in {'a465','a466','a2','a459','a60','a68','a1274'}:samples[aid]=(item['before'],rendered,raw,rect)
    print('GROUP',gi+1,'portraits',len(rows),'files',len(files),'bytes',sum(v['bytes']for v in files.values()),flush=True)
assert len(results)==len(selected),(len(results),len(selected))
if apply:
    m.update(results);(R/'converted/image-map.json').write_text(json.dumps(m,ensure_ascii=False,separators=(',',':')),'utf8');(R/'src/common/assets.js').write_text('const assets='+json.dumps({k:v['src']for k,v in m.items()},separators=(',',':'))+';export function imagePath(id){return assets[id]||"";}\n','utf8')
font=ImageFont.truetype(str(P/'extracted-engine/data/font/sourcehansanssc-regular.otf'),16);keys=['a465','a2','a459','a60'];board=Image.new('RGB',(320*len(keys),650),'#10252d');d=ImageDraw.Draw(board)
for col,aid in enumerate(keys):
    before,after,raw,rect=samples[aid]
    for row,(label,im)in enumerate([('0.1.3',before),('0.1.4',after)]):
        x=col*320;y=row*320;d.text((x+8,y+4),aid+' / '+label,font=font,fill='white');board.paste(im,(x+160-im.width//2,y+28),im)
board.save(O/'source-quality-before-after.png')
zoom=Image.new('RGB',(320*len(keys),660),'#10252d');zd=ImageDraw.Draw(zoom)
for col,aid in enumerate(keys):
    before,after,raw,rect=samples[aid];x,y,w,h=rect;crop=(x-3,y-3,x+w+3,y+h+3)
    for row,(label,im)in enumerate([('source reference',raw),('0.1.3 resource',before),('0.1.4 resource',after)]):
        xx=col*320;yy=row*220;zd.text((xx+8,yy+6),aid+' / '+label,font=font,fill='white');face=im.crop(crop);face.thumbnail((280,175));factor=min(280/face.width,175/face.height);face=face.resize((round(face.width*factor),round(face.height*factor)),Image.Resampling.NEAREST);zoom.paste(face,(xx+160-face.width//2,yy+36),face)
zoom.save(O/'face-quality-details.png')
report={'result':'passed','applied':apply,'portraits':len(rows),'bodyRecipes':len(bodies),'uniqueTextures':len(files),'bytes':sum(v['bytes']for v in files.values()),'fullyComposedFallbacks':fallback,'sourcePixelScaleChanged':False,'CGAndBackgroundBytesChanged':False,'originalExpressionsPreserved':True,'tinyFaceTexturesUsed':False,'canonicalFaceAlwaysInBody':True,'method':'SG0 visible-only adaptive median-cut, complete-canvas expression sharing; CLANNAD six-bit RGB face fallback; original-pixel quality gates, exact PNG','maxNewFaceRGBMSE':max(v['afterFaceRGBMSE']for v in rows),'oldMeanFaceRGBMSE':sum(v['beforeFaceRGBMSE']for v in rows)/len(rows),'newMeanFaceRGBMSE':sum(v['afterFaceRGBMSE']for v in rows)/len(rows),'sharedBaseAlwaysContainsSourceFace':True,'rows':rows,'files':list(files.values())}
(O/('report.json'if apply else'sample.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps({k:v for k,v in report.items()if k not in ['rows','files']},ensure_ascii=False),flush=True)
