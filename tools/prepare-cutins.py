"""Adapt original clipped portrait layers; do not flatten a view bar over a whole scene."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,io
R=Path(__file__).resolve().parents[1];P=R.parent/'parquet-probe';D=R/'src/common/cutins';D.mkdir(exist_ok=True)
ops=json.loads((R/'converted/ops.json').read_text('utf8'));m=json.loads((R/'converted/image-map.json').read_text('utf8'));plans=json.loads((R/'reports/portrait-plan.json').read_text('utf8'));ids=sorted({o['cutIn']for a in ops.values()for o in a if o.get('cutIn')},key=lambda a:int(a[1:]));cache={};boxes={}
def opened(layer):
 f=P/'decoded-layers'/Path(layer['id']).with_suffix('.png');key=str(f)
 if key not in cache:
  if len(cache)>=12:cache.clear()
  cache[key]=Image.open(f).convert('RGBA')
 return cache[key]
def blend(c,im,xy,kind,opacity):
 if opacity!=255:im=im.copy();im.putalpha(im.getchannel('A').point(lambda a:a*opacity//255))
 if kind==16:
  x,y=xy;under=c.crop((x,y,x+im.width,y+im.height));b=ImageChops.overlay(under.convert('RGB'),im.convert('RGB')).convert('RGBA');b.putalpha(im.getchannel('A'));c.alpha_composite(b,xy)
 else:assert kind==13;c.alpha_composite(im,xy)
for i,aid in enumerate(ids):
 meta=m[aid];x,y,w,h=meta.get('faceRect',meta['patchRect']);left=max(0,round(x+w/2-w*1.25));right=min(meta['width'],round(x+w/2+w*1.25));bottom=min(meta['height'],round(y+h*2.7));scale=(meta['crop'][3]-meta['crop'][1])/meta['height']
 box=[round(meta['crop'][0]+left*scale),meta['crop'][1],round(meta['crop'][0]+right*scale),round(meta['crop'][1]+bottom*scale)]
 canvas=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]))
 for layer in plans[aid]['layers']:
  if layer['left']>=box[2]or layer['top']>=box[3]or layer['left']+layer['width']<=box[0]or layer['top']+layer['height']<=box[1]:continue
  blend(canvas,opened(layer),(layer['left']-box[0],layer['top']-box[1]),layer['type'],layer['opacity'])
 canvas.thumbnail((300,190),Image.Resampling.LANCZOS);im=canvas.quantize(colors=192,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
 # Lossless palette compaction after quantization.
 counts={index:n for n,index in im.getcolors(256)};alpha=im.info.get('transparency',b'')
 # Quantize keeps alpha in the RGBA palette; read it from that palette directly.
 palette=im.getpalette('RGBA');a=lambda index:palette[index*4+3]
 originalRGBA=im.convert('RGBA').tobytes();used=sorted(counts,key=lambda index:(a(index),-counts[index],index));im=im.remap_palette(used);tr=bytes(a(index)for index in used).rstrip(b'\xff');im.info.pop('transparency',None)
 if tr:im.info['transparency']=tr
 assert im.convert('RGBA').tobytes()==originalRGBA,aid
 path=D/(aid+'.png');im.save(path,optimize=True)
 width=min(320,round(canvas.width*206/canvas.height));boxes[aid]={'src':'/common/cutins/'+aid+'.png','width':width,'height':206,'left':round((432-width)/2),'sourceCrop':box}
 if i%30==0:print('CUTINS',i,flush=True)
(R/'converted/cutin-map.json').write_text(json.dumps(boxes,ensure_ascii=False,separators=(',',':')),'utf8')
(R/'src/common/cutin-layout.js').write_text('const cutins='+json.dumps(boxes,separators=(',',':'))+";export function cutInBox(id){return cutins[id]||{src:'',width:0,height:206,left:216};}\n",'utf8')
# A compact original-style view label reserves 24px, leaving the complete CG beneath it.
u=R/'src/common/ui';src=Image.open(P/'extracted-engine/data/image/bar1.png').convert('RGBA');band=src.crop((0,0,1400,130)).resize((432,24),Image.Resampling.LANCZOS);d=ImageDraw.Draw(band);font=ImageFont.truetype(str(P/'extracted-engine/data/font/sourcehansanssc-regular.otf'),14);label='Another View';b=d.textbbox((0,0),label,font=font);d.text(((432-(b[2]-b[0]))//2,3-b[1]),label,font=font,fill='white');band.save(u/'another-banner.png',optimize=True)
shade=Image.new('RGBA',(432,286),(0,0,0,70));ImageDraw.Draw(shade).rectangle((0,44,431,263),fill=(0,0,0,255));shade.save(u/'cutin-shade.png',optimize=True)
frame=Image.new('RGBA',(432,286));d=ImageDraw.Draw(frame);d.line((0,44,431,44),fill=(45,137,154,180));d.line((0,263,431,263),fill=(45,137,154,180));frame.save(u/'cutin-frame.png',optimize=True)
for stale in D.glob('*.png'):
 if stale.stem not in boxes:
  assert stale.resolve().is_relative_to(D.resolve());stale.unlink()
report={'result':'passed','portraits':len(boxes),'bytes':sum(x.stat().st_size for x in D.glob('*.png')),'source':'original decoded PBD/TLG layers, upper-body cut-in crop','bitmapMaxHeight':190,'displayHeight':206,'anotherViewBannerHeight':24,'textAndBranchesChanged':False};(R/'reports/cutin-rendering.json').write_text(json.dumps(report,indent=2),'utf8');print(report)
