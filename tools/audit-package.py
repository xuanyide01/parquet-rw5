from pathlib import Path
import json,zipfile,io,hashlib
from PIL import Image
from fontTools.ttLib import TTFont
from rpk_signature import audit
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'src/manifest.json').read_text('utf8'));f=R/'dist'/f'{m["package"]}.debug.{m["versionName"]}.rpk'
report=audit(f);assert report['bytes']<=10000000
z=zipfile.ZipFile(f);assert json.loads(z.read('manifest-watch.json'))==m
images=0
for n in z.namelist():
 if n.startswith('common/') and not n.endswith('/'):
  assert (R/'src'/n).read_bytes()==z.read(n),n
 if n.endswith(('.png','.jpg')):
  im=Image.open(io.BytesIO(z.read(n)));im.load();images+=1
  if n.startswith('common/images/'):assert im.width<=360 and im.height<=286,n
logo=Image.open(io.BytesIO(z.read('common/logo.png')));assert logo.size==(192,192) and logo.mode=='RGBA'
assert all(logo.getpixel(pt)[3]==0 for pt in [(0,0),(191,0),(0,191),(191,191)])
cmap=TTFont(io.BytesIO(z.read('common/parquet-extra.otf'))).getBestCmap()
texts=json.loads((R/'converted/text-source.json').read_text('utf8'))
for pair in texts:
 for s in pair:assert all(c.isspace() or ord(c)<32 or c=='\ufffc' or ord(c)in cmap for c in s),repr(s)
assert not any(n.lower().endswith(('.exe','.dll','.xp3','.wav','.ogg','.mp4','.pem','.key'))for n in z.namelist())
report.update({'result':'passed','watchManifestPresentAndCorrect':True,'decodedImages':images,'allCommonResourcesMatchSource':True,'circularRGBAIcon':True,'textFontCoverageValid':True,'originalNonprintingObjectMarkers':1,'physicalDeviceTested':False})
(R/'reports/package-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report))
