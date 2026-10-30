"""Adapt PARQUET's own title art, PIMG controls and message frame to the watch."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];PROBE=ROOT.parent/'parquet-probe';SOURCE=PROBE/'extracted-engine/data';PIMG=PROBE/'uipsd-json';OUT=ROOT/'src/common/ui';OUT.mkdir(parents=True,exist_ok=True)
def original(name,id):return Image.open(PIMG/name/(str(id)+'.png')).convert('RGBA')
report={'designReference':'PARQUET original PIMG and default.tjs DefaultColors; black/cyan cut corners, no moss-green Stella theme','sources':[]}
for i,(name,left)in enumerate([('title_bg',450),('title_bg_rin',750),('title_bg_tsu',380)]):
 source=SOURCE/'image/sys'/(name+'.png');bg=Image.open(source).convert('RGB');report['sources'].append({'file':name+'.png','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'portraitCrop':[left,0,left+908,1080]})
 title=bg.crop((left,0,left+908,1080)).resize((432,514),Image.Resampling.LANCZOS).convert('RGBA');shade=Image.new('RGBA',title.size);d=ImageDraw.Draw(shade)
 for x in range(432):d.line((x,0,x,513),fill=(2,9,19,int(160*max(0,1-x/310))))
 Image.alpha_composite(title,shade).convert('RGB').save(OUT/('title-'+str(i)+'.jpg'),quality=85,optimize=True)
 thumb=bg.copy();thumb.thumbnail((144,81),Image.Resampling.LANCZOS);thumb.save(OUT/('title-thumb-'+str(i)+'.jpg'),quality=82,optimize=True)
logo=Image.open(SOURCE/'image/sys/title_logo.png').convert('RGBA').crop((1125,735,1880,990));logo.thumbnail((238,82),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(238,86));canvas.alpha_composite(logo,(0,0));canvas.save(OUT/'title-logo.png',optimize=True)
# Exact original English title lettering; baseline from the source PIMG.
meta=json.loads((PIMG/'_langdeps_en.json').read_text('utf-8-sig'));by={x['layer_id']:x for x in meta['layers']if x.get('layer_id',-1)>=0}
for key,id in [('start',2825),('side',4276),('after',2827),('load',2833),('config',2829),('extra',2830),('chapter',2831),('exit',2828)]:
 layer=original('_langdeps_en',id);scale=.83;layer=layer.resize((round(layer.width*scale),round(layer.height*scale)),Image.Resampling.LANCZOS);im=Image.new('RGBA',(202,28));im.alpha_composite(layer,(0,2+round((by[id]['top']-500)*scale)));im.save(OUT/('title-'+key+'.png'),optimize=True)
original('title',2092).resize((230,32),Image.Resampling.LANCZOS).save(OUT/'title-button.png',optimize=True)
# Watch-specific framing follows the original black panels and cyan broken outlines.
def panel(size,fill=(3,12,17),line=(24,142,152),cut=11):
 im=Image.new('RGB',size,fill);d=ImageDraw.Draw(im);w,h=size;d.line([(1,cut),(cut,1),(w-cut-1,1),(w-2,cut),(w-2,h-cut-1),(w-cut-1,h-2),(cut,h-2),(1,h-cut-1),(1,cut)],fill=line,width=1);d.line((cut+4,4,min(w-20,cut+65),4),fill=line,width=2);return im
system=panel((432,514),(2,8,13));d=ImageDraw.Draw(system);d.line([(16,86),(112,86),(121,84),(181,84)],fill=(26,124,137));d.line([(250,490),(350,490),(359,483),(416,483)],fill=(18,80,94));d.line((18,88,414,88),fill=(10,40,51));system.save(OUT/'system.png',optimize=True)
for name,size in [('quick-card',(192,60)),('choice-card',(396,108))]:panel(size,(6,23,31),(20,116,131)).save(OUT/(name+'.png'),optimize=True)
locked=panel((144,81),(5,16,23),(35,61,71));d=ImageDraw.Draw(locked);d.rounded_rectangle((61,20,83,49),radius=10,outline=(88,117,127),width=2);d.rectangle((56,35,88,59),fill=(35,61,71));d.line((72,43,72,51),fill=(143,167,176),width=2);locked.save(OUT/'title-locked.png',optimize=True)
# Strong static selection frame; keyed rows force immediate refresh on Vela.
selection=Image.new('RGBA',(124,124));sd=ImageDraw.Draw(selection);sd.rectangle((1,1,122,122),outline=(103,239,245,255),width=3);sd.polygon([(101,2),(122,2),(122,23)],fill=(103,239,245,255));sd.line((109,8,114,13,120,6),fill=(3,18,25,255),width=2);selection.save(OUT/'background-selected.png',optimize=True)
# Rebuild the message window from its own original BG/color/line and corner layers.
for name,accent,color in [('dialogue',(23,151,161),(25,126,133)),('dialogue-side',(135,123,204),(66,61,117))]:
 im=Image.new('RGBA',(432,228),(2,8,13,255));bg=original('window',89).resize((432,228),Image.Resampling.LANCZOS);im=Image.alpha_composite(im,bg)
 tint=original('window',107).resize((432,164),Image.Resampling.LANCZOS);flat=Image.new('RGBA',tint.size,color+(0,));flat.putalpha(tint.getchannel('A'));im.alpha_composite(flat,(0,0))
 for id,x in [(58,0),(61,278)]:
  deco=original('window',id).resize((154,31),Image.Resampling.LANCZOS);flat=Image.new('RGBA',deco.size,accent+(0,));flat.putalpha(deco.getchannel('A'));im.alpha_composite(flat,(x,197))
 d=ImageDraw.Draw(im);d.line((18,0,414,0),fill=accent+(255,),width=1);im.convert('RGB').save(OUT/(name+'.png'),optimize=True)
art=Image.new('RGB',(432,286),(2,8,13));art.save(OUT/'art-fill.png',optimize=True)
# The existing circular application icon is preserved across this UI-only release.
report['colors']={'normalMessage':'0x197e85','otherPerspective':'0x423d75','text':'0xffffff'}
report['titleButtonLayer']='title.pimg / 2092';report['englishTitleLabelLayers']=[2825,4276,2827,2833,2829,2830,2831,2828];report['messageLayers']=[89,107,58,61];report['uiBytes']=sum(x.stat().st_size for x in OUT.iterdir()if x.is_file());(ROOT/'reports/ui-original-reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('PARQUET_UI_READY',report['uiBytes'])
