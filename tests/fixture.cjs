const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const clean=name=>fs.readFileSync(path.join(root,'src/common',name+'.js'),'utf8').replace(/^import[^\n]*\n/gm,'').replace(/export /g,'');
const api=new Function(['catalog','chapter-label','title-background','auto-reader','text-font','portrait-layout','cutin-layout','progress','engine','saves','gallery','assets'].map(clean).join('\n')+';return {chapterLabel,cutInBox,titleBackgroundDefinitions,titleBackgroundStatus,resolveTitleBackground,checkpoint,autoSpeeds,autoWait,catalog,textFont,portraitBox,PROGRESS_KEY,emptyProgress,decodeProgress,progressFromState,withProgress,newState,restore,readFrame,readChapterSkip,next,nextChapter,choose,previous,previewMap,SLOT_COUNT,LEGACY_KEY,slotKey,decodeSave,createSave,slotRow,imagePath,groupGallery,stepVariant};')();
class Clock{
 constructor(){this.now=0;this.id=0;this.tasks=new Map();}
 set(fn,ms){const id=++this.id;this.tasks.set(id,{fn,at:this.now+Math.max(0,Number(ms)||0)});return id;}
 tick(ms){const end=this.now+ms;let count=0;while(true){const next=[...this.tasks].sort((a,b)=>a[1].at-b[1].at||a[0]-b[0])[0];if(!next||next[1].at>end)break;assert.ok(++count<20000,'timer loop');this.tasks.delete(next[0]);this.now=next[1].at;next[1].fn();}this.now=end;}
}
function fixture(values={}){
 const clock=new Clock(),data=new Map(Object.entries(values)),writes=[],events=[],files=[];let deferred=false;
 const source=fs.readFileSync(path.join(root,'src/pages/index/index.ux'),'utf8').split('<script>')[1].split('</script>')[0].replace(/^import[^\n]*\n/gm,'').replace('export default','globalThis.page=');
 const context=vm.createContext({...api,Date,console:{log:(...args)=>events.push({at:clock.now,args}),error:(...args)=>events.push({at:clock.now,args})},
  setTimeout:(fn,ms)=>clock.set(fn,ms),clearTimeout:id=>clock.tasks.delete(id),
  file:{readText:o=>{const finish=()=>o.success({text:fs.readFileSync(path.join(root,'src',o.uri),'utf8')});if(deferred)files.push(finish);else finish();}},
  storage:{get:o=>o.success(data.get(o.key)||''),set:o=>{data.set(o.key,o.value);writes.push(o);if(o.success)o.success();}},prompt:{showToast(){}}});
 vm.runInContext(source,context);const p=context.page;Object.assign(p,p.private);p.onInit();p.$element=()=>({scrollTo(){}});p.$app={exit(){events.push({at:clock.now,args:['exit']});}};
 function enter(chapter=7,cursor=0){p.stopAuto();p.clearTyping();p.session=api.newState(chapter,true);p.session.cursor=cursor;p.cachedChapter=0;p.textSpeed=0;p.renderFrame();}
 function enable(){p.showMenu();p.toggleAuto();p.resume();}
 function typed(){for(let i=0;p.timer!==null;i++){assert.ok(i<2000);clock.tick(30);}}
 return {p,clock,data,writes,events,enter,enable,typed,defer:()=>{deferred=true;},flush:()=>{deferred=false;while(files.length)files.shift()();}};
}

module.exports={api,fixture,Clock,root};
