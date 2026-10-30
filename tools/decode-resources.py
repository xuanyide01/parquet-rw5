"""Headless text/PBD/PSB resource conversion; external decoders are supplied locally."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,os
R=Path(__file__).resolve().parents[1];P=R.parent/'parquet-probe';E=P/'extracted-engine'
parser=argparse.ArgumentParser();parser.add_argument('--psb-tool',default=os.environ.get('PARQUET_PSB_TOOL',str(R.parent/'atri-tools/FreeMote/PsbDecompile.exe')));parser.add_argument('--verify-existing',action='store_true');args=parser.parse_args()
spec=importlib.util.spec_from_file_location('pbd',R/'tools/decode-pbd.py');pbd=importlib.util.module_from_spec(spec);spec.loader.exec_module(pbd)
wrapped=0
for f in E.rglob('*'):
 if not f.is_file() or f.name.endswith(('.json','.utf8.txt')):continue
 with f.open('rb')as stream:header=stream.read(5)
 if header==b'\xfe\xfe\x01\xff\xfe':
  raw=f.read_bytes()[5:];assert len(raw)%2==0
  data=bytearray()
  for at in range(0,len(raw),2):
   x=raw[at]|raw[at+1]<<8;x=((x&0xAAAA)>>1)|((x&0x5555)<<1);data.extend(x.to_bytes(2,'little'))
  text=bytes(data).decode('utf-16-le').replace('\r\n','\n').replace('\r','\n');out=f.with_name(f.name+'.utf8.txt')
  if args.verify_existing:
   old=out.read_text('utf8');assert old==text or old==text.replace('\n','\n\n'),f
  else:out.write_text(text,'utf8')
  wrapped+=1
pbds=0
for f in (E/'fgimage').rglob('*.pbd'):
 data=pbd.decode(f.read_bytes());out=f.with_suffix('.pbd.json')
 if args.verify_existing:assert json.loads(out.read_text('utf8'))==data
 else:out.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8')
 pbds+=1
counts={}
for source,pattern,dest in [('scn','*.scn','scenarios'),('evimage','*.pimg','evimage-json'),('uipsd','*.pimg','uipsd-json')]:
 files=sorted((E/source).rglob(pattern));out=P/dest;out.mkdir(exist_ok=True)
 missing=[f for f in files if not (out/(f.stem+'.json')).exists()]
 if missing:
  assert not args.verify_existing,missing
  subprocess.run([args.psb_tool,'-o',str(out),*[str(f)for f in missing]],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert all((out/(f.stem+'.json')).exists()for f in files)
 counts[source]=len(files)
report={'result':'passed','wrappedTextFiles':wrapped,'strictPbdFiles':pbds,'psbFiles':counts,'verifyExistingOnly':args.verify_existing,'desktopInputUsed':False}
(R/'reports/resource-decoding.json').write_text(json.dumps(report,indent=2),'utf8');print(report)
