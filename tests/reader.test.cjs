const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
const {api,fixture,root}=require('./fixture.cjs');
const ops=JSON.parse(fs.readFileSync(path.join(root,'converted/ops.json'),'utf8'));
function settle(s){for(let n=0;n<200;n++){const f=api.readFrame(ops[s.chapter],s);if(f.type!=='jump')return f;}throw Error('loop');}
function skip(s){const ctx=api.nextChapter(s);for(let n=0;n<20000;n++){const f=api.readChapterSkip(ops[s.chapter],s,ctx);if(f.type!=='jump'&&f.type!=='yield')return f;}throw Error('loop');}
test('all 11,098 original Chinese records survive conversion and all cross-scene edges resolve',()=>{
 const source=JSON.parse(fs.readFileSync(path.join(root,'converted/text-source.json'),'utf8')),actual=[];
 for(const [id,a]of Object.entries(ops)){assert.equal(a.length,api.catalog.scenes[id].length);for(const o of a){if(o.op==='text'){actual.push([o.speaker,o.text]);assert.ok(o.group);for(const aid of [o.background,...o.bodies])assert.ok(api.imagePath(aid));}else if(o.op==='jumpScene')assert.ok(api.catalog.scenes[o.scene]);else if(o.op==='choice')for(const i of o.items)assert.ok(api.catalog.scenes[i.scene]);}}
 assert.equal(actual.length,11098);assert.deepEqual(actual,source);
});
test('real original entry points and both after-story branches reach their own endings',()=>{
 function walk(start,choice){const s=api.newState(start,true);let lines=0;for(let n=0;n<20000;n++){const f=settle(s);if(f.type==='end')return {s,lines};if(f.type==='text'){lines++;api.next(s);}else if(f.type==='choice')api.choose(s,f.items[choice],choice);else throw Error(f.type);}throw Error('loop');}
 assert.equal(walk(api.catalog.sideInitial,0).s.chapter,4);assert.equal(walk(api.catalog.initial,0).s.chapter,92);
 for(const [choice,end]of [[0,103],[1,107]]){const {s}=walk(api.catalog.afterInitial,choice);assert.equal(s.chapter,end);assert.equal(s.variables['s015*chapter7_sel1'],choice+1);}
});
test('safe chapter skip stops at the next original chart group and never passes either pending choice',()=>{
 for(const [id,a]of Object.entries(ops))for(let i=0;i<a.length;i++){
  if(a[i].op==='text'){const s=api.newState(Number(id));s.cursor=i;settle(s);const group=s.storyGroup;const f=skip(s);assert.equal(s.choices.length,0);if(f.type==='text')assert.notEqual(s.storyGroup,group);else assert.ok(['choice','end'].includes(f.type));}
  if(a[i].op==='choice'){const s=api.newState(Number(id));s.cursor=i;const before=api.checkpoint(s);assert.equal(skip(s).type,'choice');assert.equal(s.chapter,before.chapter);assert.equal(s.cursor,before.cursor);assert.equal(s.choices.length,0);}
 }
});
test('30 independent save slots preserve pending choices, expression state and scene targets',()=>{
 assert.equal(api.SLOT_COUNT,30);assert.equal(new Set(Array.from({length:30},(_,i)=>api.slotKey(i))).size,30);
 const s=api.newState(98,true);s.variables.test=3;const raw=JSON.stringify(api.createSave(s,'choice',1000));
 for(let i=0;i<30;i++){const restored=api.decodeSave(raw);assert.equal(restored.sceneMode,'choice');assert.deepEqual(restored.state.variables,{test:3});const state=api.restore(restored.state),f=settle(state);api.choose(state,f.items[i%2],i%2);assert.equal(state.chapter,i%2?104:100);}
 assert.throws(()=>api.slotKey(30));assert.throws(()=>api.restore({...s,cursor:999999}));
});
test('chapter preview cannot unlock AFTER STORY; normal START follows original side then main sequence',()=>{
 const {p,clock}=fixture();p.textSpeed=0;p.startNew();clock.tick(0);assert.equal(p.session.chapter,3);assert.equal(p.afterUnlocked,false);
 p.session=api.newState(4,true);p.cachedChapter=0;p.renderFrame();assert.equal(p.mode,'title');assert.equal(p._progress.variables['sf.parquet_side_clear'],true);assert.equal(p.afterUnlocked,false);
 p.startNew();clock.tick(0);assert.equal(p.session.chapter,7);
 p.session=api.newState(92,false);p.cachedChapter=0;p.renderFrame();assert.equal(p.afterUnlocked,false);
 p.session=api.newState(92,true);p.cachedChapter=0;p.renderFrame();assert.equal(p.afterUnlocked,true);assert.equal(p.mode,'title');
 p.startAfterStory();clock.tick(0);assert.equal(p.session.chapter,95);
});
test('first-page route/chapter transitions use distinct keyed rows, and patches follow their body',()=>{
 const {p}=fixture();p.openChapterRoutes();const routes=JSON.parse(JSON.stringify(p.browseRows));p.selectBrowse(1);assert.equal(p.mode,'chapters');assert.notEqual(p.browseRows[0].key,routes[0].key);assert.ok(p.browseRows.length);p.closeBrowse();assert.equal(p.mode,'routes');assert.equal(p.browseRows[0].key,routes[0].key);
 const map=JSON.parse(fs.readFileSync(path.join(root,'converted/image-map.json'),'utf8'));let count=0;
 for(const [id,v]of Object.entries(map))if(v.portrait){count++;const b=api.portraitBox(id,1,0);assert.equal(b.top+b.height,286);assert.equal(b.patch,v.patch||'');assert.ok(b.patchTop>=b.top);assert.ok(b.patchHeight>0);}
 assert.equal(count,1013);
});
test('37 gallery groups hold all 367 original variants with no unresolved assets',()=>{
 const list=JSON.parse(fs.readFileSync(path.join(root,'src/common/gallery.txt'),'utf8')),groups=api.groupGallery(list);assert.equal(list.length,367);assert.equal(groups.length,37);
 for(const g of groups){assert.ok(g.variants.length);for(const v of g.variants)assert.ok(api.imagePath(v.image));}
 const map=JSON.parse(fs.readFileSync(path.join(root,'converted/image-map.json'),'utf8'));for(const v of Object.values(map))for(const f of [v.src,v.patch].filter(Boolean))assert.ok(fs.existsSync(path.join(root,'src',f)));
});
