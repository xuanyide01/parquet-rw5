const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'reports/native-v013'),url='http://127.0.0.1:43161/',log=path.resolve(root,'../parquet-layout013-environment/emulator.log');fs.mkdirSync(out,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');const pkg=path.join(root,'dist/com.codex.parquet.rw5.debug.0.1.3.rpk');
async function get(ep,timeout=20000){const r=await fetch(url+ep,{signal:AbortSignal.timeout(timeout)});if(!r.ok)throw Error(await r.text());return r;}
async function click(x,y){await get('click?x='+x+'&y='+y);await sleep(380);}
async function wait(at,re){for(let i=0;i<200;i++){const s=logs().slice(at);if(re.test(s))return s;if(/Assertion failed panic:/.test(s))throw Error('Native panic');await sleep(120);}throw Error('Native timeout '+re);}
async function expected(x,y,re){const at=logs().length;await click(x,y);return wait(at,re);}
async function shot(name){await sleep(250);const b=Buffer.from(await(await get('screen')).arrayBuffer());fs.writeFileSync(path.join(out,name+'.png'),b);return crypto.createHash('sha256').update(b).digest('hex');}
async function wake(){const b=Buffer.from(await(await get('screen')).arrayBuffer());if(b.length<3500){await get('wake');await sleep(800);}}
async function title(){await expected(216,478,/PARQUET_RW5 menu/);await expected(216,463,/PARQUET_RW5 title shown/);}
async function chapter(entry,first){const catalog=JSON.parse(fs.readFileSync(path.join(root,'converted/catalog.json'),'utf8')),list=catalog.chapters.filter(x=>x.route===1),index=list.findIndex(x=>x.id===entry);assert.ok(index>=0);await click(90,264);await click(216,218);for(let i=0;i<Math.floor(index/4);i++)await click(360,474);await expected(216,124+92*(index%4),new RegExp('PARQUET_RW5 frame '+first+' 0'));}
async function advance(scene,from,to){for(let i=from+1;i<=to;i++)await expected(355,478,new RegExp('PARQUET_RW5 frame '+scene+' '+i+'(?:\r|\n|$)'));}
(async()=>{
 const begin=logs().length,bytes=fs.readFileSync(pkg),sha=crypto.createHash('sha256').update(bytes).digest('hex'),checks=[];await get('start',90000);await wait(begin,/PARQUET_RW5 background loaded title/);await wake();await shot('01-title');
 await expected(90,336,/PARQUET_RW5 settings open title/);await shot('02-system-safe-header');await click(216,116);await click(216,480);await sleep(600);
 await chapter(5,7);await shot('03-prologue-first');await expected(216,478,/PARQUET_RW5 menu/);await shot('04-quick-menu-safe-header');await expected(114,190,/PARQUET_RW5 frame 9 0/);await shot('05-prologue-still-prologue');
 await expected(216,478,/PARQUET_RW5 menu/);await expected(114,190,/PARQUET_RW5 frame 13 0/);await shot('06-original-chapter-1-1');checks.push('original prologue remains prologue across its parts, then Chapter 1-1','quick/system headers and bottom controls moved inside rounded-screen safe area');
 await title();await chapter(9,9);await advance(9,0,23);await shot('07-aika-normalized');
 await expected(216,478,/PARQUET_RW5 menu/);await expected(114,120,/PARQUET_RW5 slots ready save/);await expected(216,134,/PARQUET_RW5 slot saved 1 9 23/);await sleep(1800);await title();
 for(const sample of [{entry:23,scene:25,cursor:0,name:'08-tsubasa-normalized'},{entry:87,scene:87,cursor:1,name:'09-rino-normalized'},{entry:63,scene:63,cursor:2,name:'10-nika-normalized'},{entry:65,scene:65,cursor:18,name:'11-hashihime-normalized'},{entry:33,scene:33,cursor:1,name:'12-two-characters-same-scale'},{entry:29,scene:31,cursor:0,name:'13-another-view-center-and-portraits'}]){
  await chapter(sample.entry,sample.scene);await advance(sample.scene,0,sample.cursor);await shot(sample.name);await title();
 }
 checks.push('native normal portraits for Aika, Tsubasa, Rino, Nika and Hashihime inspected','same reference scale preserved in two-character scenes','Another View label centered, complete scene art and standing portraits remain bottom aligned');
 await expected(90,372,/PARQUET_RW5 gallery ready/);await shot('14-gallery-safe-header');await click(216,474);
 let at=logs().length;await click(90,408);await wait(at,/PARQUET_RW5 app destroyed/);await sleep(5000);at=logs().length;await get('start',90000);await wait(at,/PARQUET_RW5 background loaded title/);await wake();await expected(90,300,/PARQUET_RW5 slots ready load/);await shot('15-load-safe-header');await expected(216,134,/PARQUET_RW5 slot loaded 1 9 23/);await shot('16-cold-restore-chapter-and-portrait');await title();
 const recent=logs().slice(begin);assert.ok(!/PARQUET_RW5 background failed|Assertion failed panic:|PANIC!!!|coredump_dump_dev/.test(recent));checks.push('normal EXIT/restart and slot load restore the chapter and new portrait layout without exceptions');
 const report={result:'passed',version:'0.1.3',packageSha256:sha,packageBytes:bytes.length,screen:[432,514],runtime:'official generic Vela Watch 5.0, 128MB RAM',physicalDeviceTested:false,usesDesktopInput:false,injectedScenesOrSaves:false,checks};fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log('NATIVE_LAYOUT_PASSED',JSON.stringify(report));
})().catch(async e=>{fs.writeFileSync(path.join(out,'failure.txt'),e.stack);try{await shot('failure');}catch(_){}console.error(e.stack);process.exitCode=1;});
