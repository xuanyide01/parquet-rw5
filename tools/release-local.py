"""Package only the app, conversion sources and relevant passed evidence for local review."""
from pathlib import Path
import json,hashlib,zipfile,shutil
R=Path(__file__).resolve().parents[1];OUT=R.parent.parent/'outputs';OUT.mkdir(exist_ok=True)
m=json.loads((R/'src/manifest.json').read_text('utf8'));version=m['versionName'];stem='PARQUET-RW5-'+version
f=R/'dist'/f'{m["package"]}.debug.{version}.rpk';data=f.read_bytes();digest=hashlib.sha256(data).hexdigest()
checks={key:json.loads((R/'reports'/file).read_text('utf8'))for key,file in [('extraction','engine-export.json'),('source','source-equivalence.json'),('images','images.json'),('font','text-font.json'),('regression','regression-tests.json'),('package','package-audit.json'),('originalTitleRules','title-background-source-audit.json'),('originalUI','ui-original-reference.json'),('nativeFinal','native-v015/report.json'),('v015Scope','v015-scope-audit.json'),('staticCompression','static-compression-v015.json'),('userAcceptance','user-acceptance-v015.json'),('portraitQuality','portrait-quality-audit.json'),('chapterLabels','chapter-label-source-audit.json'),('layoutControlFlow','layout-control-flow-audit.json'),('portraitScale','portrait-scale-audit.json'),('sceneVisuals','scene-visual-source-audit.json'),('visualControlFlow','scene-visual-control-flow-audit.json')]}
assert checks['nativeFinal']['packageSha256']==digest==checks['package']['sha256']
assert all(checks[x]['result']=='passed'for x in ['source','regression','package','nativeFinal','sceneVisuals','visualControlFlow','chapterLabels','layoutControlFlow','portraitScale','portraitQuality','v015Scope','staticCompression','userAcceptance'])
assert len(data)<10000000
checks['extraction']={k:v for k,v in checks['extraction'].items()if k!='resources'}
report={'application':'《PARQUET》','version':version,'target':'REDMI Watch 5 · 432×514','bytes':len(data),'decimalMB':round(len(data)/1000000,2),'sha256':digest,'physicalDeviceTested':False,'userAcceptancePassed':True,'userAcceptance':checks['userAcceptance'],'checks':checks}
(R/'reports/final-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
for suffix in ['.bin','.rpk']:(OUT/(stem+suffix)).write_bytes(data)
shutil.copyfile(R/'reports/final-report.json',OUT/(stem+'-检查报告.json'));shutil.copyfile(R/'README.md',OUT/(stem+'-安装说明.md'))
tools={'audit-package.py','audit-source.py','build-font.py','build.cjs','convert-story.py','decode-layers.ps1','decode-pbd.py','decode-resources.py','emulator-server.cjs','emulator-view.html','extract-engine.py','generate-layout.py','native-ui-v011.cjs','native-polish-v011.cjs','native-ui-install.cjs','optimize-pngs.py','plan-portraits.py','prepare-images.py','prepare-ui.py','prepare-cutins.py','native-visual-v012.cjs','native-layout-v013.cjs','native-final-v013.cjs','native-portraits-v014.cjs','improve-portraits.py','portrait-codec.py','audit-portrait-quality.py','compress-static-v015.py','audit-v015.py','native-title-v015.cjs','native-title-qa-v015.cjs','build-title-qa-v015.py','release-local.py','repack-rpk.cjs','rpk_signature.py','setup-emulator.cjs','tjs_data.py','xp3.py'}
reports={'engine-export.json','engine-export-manifest.json','resource-decoding.json','source-comparison.json','source-equivalence.json','story-conversion.json','portrait-plan.json','tlg-plan.json','images.json','image-errors.json','portrait-errors.json','lossless-image-optimization.json','text-font.json','regression-tests.json','package-audit.json','title-background-source-audit.json','ui-original-reference.json','ui-polish-scope.json','scene-visual-source-audit.json','scene-visual-control-flow-audit.json','cutin-rendering.json','chapter-label-source-audit.json','layout-control-flow-audit.json','portrait-scale-audit.json','portrait-scale-before-after.png','portrait-quality-audit.json','regression-v014.log','regression-v015.log','v015-scope-audit.json','static-compression-v015.json','user-acceptance-v015.json','final-report.json'}
files=[]
for file in R.rglob('*'):
 if not file.is_file():continue
 rel=file.relative_to(R);a=rel.parts
 keep=(len(a)==1 and file.name in {'README.md','LICENSE','THIRD_PARTY_NOTICES.md','package.json','quickapp.config.js','CHANGELOG.md','.gitignore'})or a[0]in {'src','tests','docs','licenses','converted'}or (a[0]=='tools'and len(a)==2 and file.name in tools)or (a[0]=='reports'and ((len(a)==2 and file.name in reports)or (len(a)>2 and ((a[1]=='native-v015'and (file.suffix in {'.json','.png'}or file.name=='installation-wait-timeout.txt'))or(a[1]=='portrait-quality-v014'and file.name in {'report.json','source-quality-before-after.png','face-quality-details.png'})))))
 if keep and '__pycache__'not in a and file.suffix.lower()not in {'.exe','.dll','.pem','.key','.xp3','.pyc'}:files.append(file)
archive=OUT/(stem+'-源码.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for file in files:z.write(file,stem+'/'+file.relative_to(R).as_posix())
with zipfile.ZipFile(archive)as z:
 assert z.testzip()is None
 assert not any(n.lower().endswith(('.exe','.dll','.pem','.key','.xp3','.pyc'))for n in z.namelist())
sha=[]
for file in [OUT/(stem+'.bin'),OUT/(stem+'.rpk'),archive,OUT/(stem+'-安装说明.md'),OUT/(stem+'-检查报告.json')]:sha.append(hashlib.sha256(file.read_bytes()).hexdigest()+'  '+file.name)
(OUT/(stem+'-SHA256.txt')).write_text('\n'.join(sha)+'\n','utf8')
for source,label in [('01-title-smaller-logo.png','标题预览'),('11-tsubasa-selected-highlight.png','背景设置预览'),('04-unchanged-waiter-face.png','立绘预览')]:shutil.copyfile(R/'reports/native-v015'/source,OUT/(stem+'-'+label+'.png'))
print(json.dumps({'version':version,'bytes':len(data),'MB':round(len(data)/1000000,2),'sha256':digest,'sourceFiles':len(files),'sourceArchiveBytes':archive.stat().st_size,'output':str(OUT)},ensure_ascii=False))
