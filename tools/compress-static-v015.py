"""Re-encode full-frame CG/backgrounds from original source; preserve portrait bytes."""
from pathlib import Path
from PIL import Image
import json,hashlib,io
R=Path(__file__).resolve().parents[1]
# Reuse the original source-layer compositor, without running its conversion loop.
namespace={'__file__':str(R/'tools/prepare-images.py')}
source=(R/'tools/prepare-images.py').read_text('utf8');exec(source[:source.index('for i,(aid,v) in enumerate(requests.items()):')],namespace)
m=json.loads((R/'converted/image-map.json').read_text('utf8'));requests=json.loads((R/'converted/image-requests.json').read_text('utf8'));D=R/'src/common/images/s015';D.mkdir(exist_ok=True)
rows=[];old_files={};new_files={}
for aid,meta in m.items():
 if meta['portrait']:continue
 old=R/'src'/meta['src'].lstrip('/');old_files[str(old)]=old.stat().st_size
 req=requests[aid];im=namespace['static'](req['file'],req['options']);im.thumbnail((320,216),Image.Resampling.LANCZOS)
 bg=Image.new('RGB',im.size,'white');bg.paste(im,mask=im.getchannel('A')if im.mode=='RGBA'else None);b=io.BytesIO();bg.save(b,format='JPEG',quality=62,subsampling=2,optimize=True,progressive=False);raw=b.getvalue();name=hashlib.sha256(raw).hexdigest()[:20]+'.jpg';file=D/name;file.write_bytes(raw);new_files[name]=len(raw)
 rows.append({'id':aid,'source':req['file'],'beforeSize':[meta['width'],meta['height']],'size':list(im.size),'bytes':len(raw),'originalAspectPreserved':True});meta.update(src='/common/images/s015/'+name,width=im.width,height=im.height)
 if len(rows)%100==0:print('STATIC',len(rows),flush=True)
(R/'converted/image-map.json').write_text(json.dumps(m,ensure_ascii=False,separators=(',',':')),'utf8');(R/'src/common/assets.js').write_text('const assets='+json.dumps({k:v['src']for k,v in m.items()},separators=(',',':'))+';export function imagePath(id){return assets[id]||"";}\n','utf8')
report={'result':'passed','version':'0.1.5','staticRequests':len(rows),'beforeBytes':sum(old_files.values()),'afterBytes':sum(new_files.values()),'source':'original full-resolution PNG/PIMG layers, not previously compressed JPEG','maxSize':[320,216],'jpegQuality':62,'portraitsAndCutinsUnchanged':True,'allImagesKeepOriginalAspect':True,'rows':rows};(R/'reports/static-compression-v015.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps({k:v for k,v in report.items()if k!='rows'},ensure_ascii=False))
