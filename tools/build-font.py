from pathlib import Path
import json
from fontTools import subset
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
source=ROOT.parent/'parquet-probe/extracted-engine/data/font/sourcehansanssc-regular.otf'
chars=set(chr(x) for x in range(32,127))
def collect(v):
 if isinstance(v,str):chars.update(v)
 elif isinstance(v,list):
  for x in v:collect(x)
 elif isinstance(v,dict):
  for x in v.values():collect(x)
collect(json.loads((ROOT/'converted/text-source.json').read_text('utf8')))
collect(json.loads((ROOT/'converted/catalog.json').read_text('utf8')))
for file in (ROOT/'src').rglob('*'):
 if file.suffix in ('.js','.ux'):chars.update(file.read_text('utf8'))
chars.discard('\ufeff');chars.discard('\ufffc') # original contains one nonprinting object replacement marker
f=TTFont(source);cmap=f.getBestCmap()
missing=sorted(c for c in chars if not c.isspace() and ord(c)>=32 and ord(c) not in cmap)
assert not missing,repr(missing)
coverage={ord(c) for c in chars if ord(c) in cmap}
opt=subset.Options();opt.layout_features=[];opt.drop_tables+=['BASE','GSUB','GPOS','VORG','vhea','vmtx']
s=subset.Subsetter(options=opt);s.populate(unicodes=coverage);s.subset(f)
for name in f['name'].names:
 if name.nameID in (1,3,4,6,16):name.string='ParquetWatchText'.encode(name.getEncoding(),errors='replace')
if 'CFF ' in f:f['CFF '].cff.fontNames=['ParquetWatchText']
out=ROOT/'src/common/parquet-extra.otf';f.save(out)
assert coverage==set(TTFont(out).getBestCmap())
assert out.stat().st_size<1500000
report={'family':'ParquetWatchText','codepoints':len(coverage),'fontBytes':out.stat().st_size,'allStoryTextCovered':True,'license':'SIL OFL 1.1','source':'Original bundled SourceHanSansSC-Regular','renamedSubset':True}
(ROOT/'reports/text-font.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(report)
