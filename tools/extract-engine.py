"""Headless export through the supplied engine; verify every file against XP3 adlr."""
from pathlib import Path
import sys,json,subprocess,time,zlib,hashlib
from xp3 import index
root=Path(__file__).absolute().parents[1];probe=root.parent/'parquet-probe';game=probe/'game';out=probe/'extracted-engine';out.mkdir(parents=True,exist_ok=True);(probe/'batch').mkdir(exist_ok=True)
exts={'.scn','.ks','.tjs','.txt','.csv','.ini','.stage','.stand','.sinfo','.pbd','.asd','.func','.event','.psb','.pimg','.png','.tlg','.otf','.ttf'}
entries=[];archives=[];jobs=[]
for name in ['main','scn','data','bgimage','fgimage','evimage','uipsd']:
 arc=game/(name+'.xp3');items=index(arc)
 archives.append({'archive':arc.name,'bytes':arc.stat().st_size,'sha256':hashlib.sha256(arc.read_bytes()).hexdigest(),'items':len(items)-1})
 for item in items[1:]:
  if Path(item['name']).suffix.lower() not in exts:continue
  dest=(out/name/item['name']).absolute();assert dest.is_relative_to(out.absolute())
  dest.parent.mkdir(parents=True,exist_ok=True)
  uri='file://./'+arc.as_posix()[0].lower()+arc.as_posix()[2:]+'>'+item['name']
  entries.append({**item,'archive':arc.name,'output':dest.relative_to(out).as_posix()})
  jobs.append([uri,dest.as_posix()])
status=probe/'batch/export-all-status.txt';progress=probe/'batch/export-progress.txt'
script='Plugins.link("plugin/PackinOne.dll");\nvar jobs='+json.dumps(jobs,ensure_ascii=False)+';\nvar log=[];\n'
script+='for(var i=0;i<jobs.count;i++){ try { Storages.exportFile(jobs[i][0],jobs[i][1]); log.add("OK "+i); } catch(e) { log.add("ERROR "+i+" "+e.message); } if(i%50==0) { var p=["exported="+i+"/"+jobs.count];p.save('+json.dumps(progress.as_posix())+'); } }\n'
script+='log.save('+json.dumps(status.as_posix())+');System.exit();\n'
p=game/'resource-export-all.tjs';p.write_text(script,'utf-16')
(root/'reports').mkdir(exist_ok=True)
(root/'reports/engine-export-manifest.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),'utf8')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
args=[str(game/'PARQUET.exe'),'-startup='+str(p),'-datapath='+str(probe/'batch/savedata'),'-forcelog=yes','-logerror=no','-gclim=16']
proc=subprocess.Popen(args,cwd=game,startupinfo=si,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'event':'export_started','pid':proc.pid,'resources':len(jobs)}),flush=True)
last=''
while proc.poll() is None:
 time.sleep(1)
 if progress.exists():
  try:s=progress.read_text('utf-16').strip()
  except (UnicodeError,OSError):continue
  if s!=last:print(s,flush=True);last=s
assert proc.returncode==0,proc.returncode
log=status.read_text('utf-16');errors=[line for line in log.splitlines() if line.startswith('ERROR')]
assert not errors,errors[:5]
verified=[]
for item in entries:
 dest=out/item['output'];data=dest.read_bytes();expected=sum(s[2] for s in item['segments'])
 assert len(data)==expected,(item['output'],len(data),expected)
 assert zlib.adler32(data)&0xffffffff==item['adler'],item['output']
 verified.append({'file':item['output'],'bytes':len(data),'adler32':item['adler'],'sha256':hashlib.sha256(data).hexdigest()})
report={'result':'passed','method':'original-engine headless startup batch with built-in PackinOne Storages.exportFile; independent XP3 adlr and size checks','originalGameDirectoriesReadOnly':True,'desktopAutomationUsed':False,'gameplayScriptsExecuted':False,'archives':archives,'verifiedFiles':len(verified),'resources':verified}
(root/'reports/engine-export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'event':'export_verified','resources':len(verified),'bytes':sum(x['bytes'] for x in verified)}),flush=True)
