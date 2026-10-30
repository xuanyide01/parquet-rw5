const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),url='http://127.0.0.1:43135/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function get(endpoint){const r=await fetch(url+endpoint,{signal:AbortSignal.timeout(180000)});const text=await r.text();if(!r.ok)throw Error(text);return text;}
(async()=>{
 // Registry readiness precedes the booting AMS installation service.
 console.log('WAITING_FOR_BOOT_SERVICES');
 const environment=path.resolve(root,'../parquet-after-environment'),record=JSON.parse(fs.readFileSync(path.join(environment,'controller-pid.json'))),bootLog=path.join(environment,'emulator.log');
 let bootReady=false;for(let i=0;i<900;i++){if(fs.existsSync(bootLog)&&/Startup home app failure/.test(fs.readFileSync(bootLog).subarray(record.logOffset||0).toString('utf8'))){bootReady=true;break;}await sleep(200);}
 if(!bootReady)throw Error('Cold-boot installation services did not become ready');await sleep(2000);
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8'));
 const rpk=path.join(root,'dist',manifest.package+'.debug.'+manifest.versionName+'.rpk');
 for(let attempt=1;!process.argv.includes('--start-only')&&attempt<=3;attempt++){
  try{console.log('INSTALL',await get('install?rpk='+encodeURIComponent(rpk)));break;}
  catch(e){if(attempt===3)throw e;console.log('INSTALL_SERVICE_RETRY',attempt,e.message);await sleep(10000);}
 }
 const log=path.resolve(root,'../parquet-after-environment/emulator.log'),at=fs.readFileSync(log,'utf8').length;
 console.log('START',await get('start'));
 let ready=false;
 for(let i=0;i<100;i++){
  const recent=fs.readFileSync(log,'utf8').slice(at);
  if(/PARQUET_RW5 background loaded title/.test(recent)&&/PageCallHook, name:onShow/.test(recent)){ready=true;break;}
  await sleep(250);
 }
 if(!ready)throw Error('New title did not complete onShow');console.log('START_DOM_READY');await sleep(500);
})().catch(e=>{console.error(e.message);process.exitCode=1;});
