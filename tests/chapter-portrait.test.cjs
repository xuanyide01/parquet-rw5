const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
const {api,fixture,root}=require('./fixture.cjs'),ops=JSON.parse(fs.readFileSync(path.join(root,'converted/ops.json'),'utf8'));
test('actual original chapter tags fix the prologue/CHAPTER 1 display sequence',()=>{
 const f=fixture();for(const [scene,expected]of [[3,'pre story'],[7,'prologue'],[9,'prologue'],[13,'CHAPTER 1-1'],[17,'CHAPTER 1-2'],[21,'CHAPTER 2-1'],[31,'CHAPTER 2-4'],[91,'epilogue'],[95,'AFTER STORY']]){f.enter(scene);assert.equal(f.p.chapterLabel,expected);}
 const main=api.catalog.chapters.filter(x=>x.route===1).map(x=>x.name),unique=main.filter((n,i)=>i===0||n!==main[i-1]);assert.equal(unique[0],'prologue');assert.equal(unique[1],'CHAPTER 1-1');assert.equal(unique[2],'CHAPTER 1-2');assert.equal(unique.at(-1),'epilogue');
});
test('all original text frames have an original chapter name and old saves have a correct fallback',()=>{
 let count=0;for(const [id,a]of Object.entries(ops))for(let i=0;i<a.length;i++)if(a[i].op==='text'){const s=api.newState(Number(id));s.cursor=i;api.readFrame(a,s);assert.ok(api.catalog.chapterLabels[s.chapterTag]);assert.equal(api.chapterLabel(s),api.catalog.chapterLabels[a[i].chapterTag]);count++;}
 assert.equal(count,11098);const old=api.newState(7,true);delete old.chapterTag;assert.equal(api.chapterLabel(api.restore(old)),'prologue');const saved=api.createSave(old,'play',0);assert.match(api.slotRow(0,saved).meta,/prologue/);
});
test('normal standing portraits use the same facial scale in single/multi and normal/Another View scenes',()=>{
 const map=JSON.parse(fs.readFileSync(path.join(root,'converted/image-map.json'),'utf8'));let count=0;
 for(const [id,m]of Object.entries(map))if(m.portrait){count++;assert.equal(m.height,262);assert.ok(Math.abs(m.sourceScale-.15)<.0001);for(const n of [1,2,3])for(const top of [0,24]){const box=api.portraitBox(id,n,0,top);assert.equal(box.height,262);assert.equal(box.top,24);assert.equal(box.top+box.height,286);assert.ok(Math.abs(box.faceReferenceHeight-m.faceReferenceHeight)<.001);assert.ok(Math.abs(box.left+m.faceAnchor[0]-(n===1?216:n===2?126:90))<=.51);}}
 assert.equal(count,1013);
});
