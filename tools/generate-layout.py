from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'converted/image-map.json').read_text('utf8'))
portraits={k:[v['width'],v['height'],v.get('patch',''),v.get('patchRect',[0,0,0,0]),v.get('faceAnchor',[v['width']/2,64])[0],v.get('faceReferenceHeight',40)]for k,v in m.items()if v.get('portrait')}
f=R/'src/common/portrait-layout.js';s=f.read_text('utf8');tail=s[s.index('export function portraitBox'):];f.write_text('const portraits='+json.dumps(portraits,separators=(',',':'))+';\n'+tail,'utf8')
# Remove stale generated encodings only after successful mapping; never touch source assets.
D=R/'src/common/images';keep={v[k]for v in m.values()for k in ['src','patch']if v.get(k)}
for file in D.rglob('*'):
 if file.is_file() and '/'+file.relative_to(R/'src').as_posix()not in keep:
  assert file.resolve().is_relative_to(D.resolve());file.unlink()
f=R/'reports/images.json';report=json.loads(f.read_text('utf8'));report['bytes']=sum(f.stat().st_size for f in D.rglob('*')if f.is_file());report['portraitCrop']='uniform original-canvas pixel scale; 262px body bitmap; bottom aligned';f.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(report)
