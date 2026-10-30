from pathlib import Path
from PIL import Image
import io,json
R=Path(__file__).resolve().parents[1];before=after=count=0
for f in (R/'src/common/images').rglob('*.png'):
 raw=f.read_bytes();im=Image.open(io.BytesIO(raw));im.load()
 if im.mode!='P':continue
 colors={index:n for n,index in im.getcolors(256)};alpha=im.info.get('transparency',b'')
 if isinstance(alpha,int):a=lambda x:0 if x==alpha else 255
 else:a=lambda x:alpha[x]if x<len(alpha)else 255
 used=sorted(colors,key=lambda x:(a(x),-colors[x],x));compact=im.remap_palette(used)
 transparency=bytes(a(i)for i in used).rstrip(b'\xff')
 compact.info.pop('transparency',None)
 if transparency:compact.info['transparency']=transparency
 b=io.BytesIO();compact.save(b,format='PNG',optimize=True);new=b.getvalue()
 assert Image.open(io.BytesIO(new)).convert('RGBA').tobytes()==im.convert('RGBA').tobytes(),f
 if len(new)<len(raw):f.write_bytes(new);before+=len(raw);after+=len(new);count+=1
report={'result':'passed','filesReduced':count,'bytesRemoved':before-after,'decodedRGBAIdentical':True,'method':'Remove unused palette entries and trailing opaque alpha entries, reorder palette without changing pixels'}
(R/'reports/lossless-image-optimization.json').write_text(json.dumps(report,indent=2),'utf8');print(report)
