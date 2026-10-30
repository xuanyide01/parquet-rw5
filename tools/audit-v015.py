"""Check 0.1.5 compression preserves portrait bytes and original story/choices."""
from pathlib import Path
from PIL import Image
import json,zipfile,hashlib
R=Path(__file__).resolve().parents[1];m=json.loads((R/'converted/image-map.json').read_text('utf8'));count=0;files=set();statics=0
with zipfile.ZipFile(R.parent.parent/'outputs/PARQUET-RW5-0.1.4-源码.zip')as z:
 old=json.loads(z.read('PARQUET-RW5-0.1.4/converted/image-map.json'))
 for aid,v in m.items():
  if v['portrait']:
   count+=1;assert v==old[aid],aid
   for key in ['src','patch']:
    if v.get(key):
     p=R/'src'/v[key].lstrip('/');assert p.read_bytes()==z.read('PARQUET-RW5-0.1.4/src'+v[key]);files.add(v[key])
  else:
   statics+=1;im=Image.open(R/'src'/v['src'].lstrip('/'));im.load();assert im.size==(v['width'],v['height'])and im.width<=320 and im.height<=216
   assert abs(v['width']*old[aid]['height']-v['height']*old[aid]['width'])<=max(v['width'],v['height'])+max(old[aid]['width'],old[aid]['height'])
 for relative in ['converted/ops.json','converted/catalog.json','src/common/gallery.txt','src/common/engine.js','src/common/saves.js','src/common/progress.js','src/common/portrait-layout.js','src/common/cutin-layout.js']:
  assert (R/relative).read_bytes()==z.read('PARQUET-RW5-0.1.4/'+relative),relative
 for p in (R/'src/common/cutins').rglob('*.png'):assert p.read_bytes()==z.read('PARQUET-RW5-0.1.4/'+p.relative_to(R).as_posix())
assert count==1013
report={'result':'passed','version':'0.1.5','baseline':'0.1.4','portraitRequests':count,'portraitFilesWithIdenticalBytes':len(files),'cutinsWithIdenticalBytes':True,'originalPortraitScaleAndAnchorsIdentical':True,'staticRequestsFromOriginalSource':statics,'staticMaxSize':[320,216],'fullImageAspectPreserved':True,'textChoicesSceneIdsGallerySaveSchemaAndProgressSchemaIdentical':True,'physicalDeviceTested':False}
(R/'reports/v015-scope-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False))
