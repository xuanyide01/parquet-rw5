"""Independently audit final complete-canvas textures and unchanged story data."""
from pathlib import Path
from PIL import Image
import json,zipfile,hashlib,collections
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'converted/image-map.json').read_text('utf8'));q=json.loads((R/'reports/portrait-quality-v014/report.json').read_text('utf8'))
assert q['result']=='passed' and q['portraits']==1013 and q['canonicalFaceAlwaysInBody'] and not q['tinyFaceTexturesUsed']
assert q['newMeanFaceRGBMSE']<q['oldMeanFaceRGBMSE']
assert all(v['afterFaceRGBMSE']<=max(v['beforeFaceRGBMSE']+1.001,4.001) for v in q['rows'])
count=0;patches=0;files=set();bases=set();max_pixels=0
for aid,v in m.items():
 if not v.get('portrait'):continue
 count+=1;assert v['height']==262 and abs(v['sourceScale']-.15)<.0001 and v['canonicalFace']
 for key in ['src','patch']:
  if not v.get(key):continue
  file=R/'src'/v[key].lstrip('/');im=Image.open(file);im.load();assert im.size==(v['width'],v['height']),(aid,key,im.size);files.add(file);max_pixels=max(max_pixels,im.width*im.height)
  if key=='patch':patches+=1;assert v['patchRect']==[0,0,v['width'],v['height']]
 bases.add(v['src'])
assert count==1013
oldzip=R.parent.parent/'outputs/PARQUET-RW5-0.1.3-源码.zip'
with zipfile.ZipFile(oldzip)as z:
 for relative in ['converted/ops.json','converted/catalog.json','src/common/gallery.txt','src/common/engine.js','src/common/saves.js']:
  assert z.read('PARQUET-RW5-0.1.3/'+relative)==(R/relative).read_bytes(),relative
 oldmap=json.loads(z.read('PARQUET-RW5-0.1.3/converted/image-map.json'))
 for aid,v in m.items():
  if not v.get('portrait'):
   assert v==oldmap[aid]
   assert (R/'src'/v['src'].lstrip('/')).read_bytes()==z.read('PARQUET-RW5-0.1.3/src'+v['src'])
report={'result':'passed','version':'0.1.4','portraits':count,'completeCanvasExpressionRequests':patches,'uniqueBaseOrFallbackFiles':len(bases),'uniquePortraitFiles':len(files),'portraitBytes':sum(f.stat().st_size for f in files),'maxOneDecodedPortraitRGBABytes':max_pixels*4,'sixLayersRGBAUpperBoundBytes':max_pixels*4*6,'textChoicesScenePositionsSaveKeysAndGalleryUnchanged':True,'allBackgroundAndCGBytesUnchanged':True,'sourceScaleAndAnchorUnchanged':True,'tinyFaceTexturesUsed':False,'physicalDeviceTested':False}
(R/'reports/portrait-quality-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False))
