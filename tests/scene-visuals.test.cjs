const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
const {api,fixture,root}=require('./fixture.cjs'),ops=JSON.parse(fs.readFileSync(path.join(root,'converted/ops.json'),'utf8')),images=JSON.parse(fs.readFileSync(path.join(root,'converted/image-requests.json'),'utf8'));
function frame(id,index){const s=api.newState(id);s.cursor=index;api.readFrame(ops[id],s);return s;}
test('the reported Another View scene restores the original cabaret instead of a UI bar',()=>{
 const f=frame(31,2);assert.equal(f.view,'another');assert.equal(images[f.background].file,'特殊_キャバクラ');assert.ok(!['bar1','bar2'].includes(images[f.background].file));
});
test('all 695 Another View records retain scene art and every original CG is available',()=>{
 let count=0,cgs=0;for(const a of Object.values(ops))for(const o of a)if(o.op==='text'&&o.view==='another'){count++;assert.ok(!['bar1','bar2','回想枠'].includes(images[o.background].file));if(/^ev\d/i.test(images[o.background].file))cgs++;assert.ok(api.imagePath(o.background));}
 assert.equal(count,695);assert.ok(cgs>50);
});
test('Aika call enters the original dark cut-in, changes expression and clears it at scene transitions',()=>{
 assert.equal(frame(21,18).cutIn,'');const a=frame(21,22),b=frame(21,25);assert.equal(images[a.background].file,'倉庫_リビングa');assert.equal(images[a.cutIn].file,'愛花.stand');assert.equal(images[a.cutIn].options.face,'23');assert.equal(a.cutInOpacity,200);assert.equal(images[b.cutIn].options.face,'22');assert.notEqual(a.cutIn,b.cutIn);assert.ok(api.cutInBox(a.cutIn).src);assert.equal(frame(21,39).cutIn,'');assert.equal(frame(21,39).cutInOpacity,0);
});
test('view and call layout change per frame, reserve banner space and survive old-state restore',()=>{
 const f=fixture(),{p}=f;f.enter(31,2);assert.equal(p.anotherView,true);assert.equal(p.sceneArtTop,24);assert.equal(p.sceneArtHeight,262);assert.equal(p.dialogueFrameSrc,'/common/ui/dialogue-side.png');
 f.enter(21,22);assert.equal(p.anotherView,false);assert.equal(p.sceneArtTop,0);assert.ok(p.cutInSrc);assert.equal(p.cutInOpacity,200/255);f.enter(21,39);assert.equal(p.cutInSrc,'');assert.equal(p.sceneArtHeight,286);
 const old=api.newState(21);delete old.view;delete old.cutIn;delete old.cutInOpacity;const restored=api.restore(old);assert.equal(restored.view,'normal');assert.equal(restored.cutIn,'');
});
test('view banner keeps standing art attached to dialogue, and every cut-in file exists',()=>{
 const map=JSON.parse(fs.readFileSync(path.join(root,'converted/image-map.json'),'utf8'));for(const [id,m]of Object.entries(map))if(m.portrait){const b=api.portraitBox(id,1,0,24);assert.equal(b.top+b.height,286);assert.ok(b.top>=24);}
 const cutins=JSON.parse(fs.readFileSync(path.join(root,'converted/cutin-map.json'),'utf8'));assert.ok(Object.keys(cutins).length>100);for(const m of Object.values(cutins))assert.ok(fs.existsSync(path.join(root,'src',m.src)));
});
