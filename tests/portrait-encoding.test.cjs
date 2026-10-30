const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
const {api,fixture,root}=require('./fixture.cjs');
const images=JSON.parse(fs.readFileSync(path.join(root,'converted/image-map.json'),'utf8'));
test('reported missing-face frame and every expression use complete portrait canvases',()=>{
 let count=0;for(const [id,m]of Object.entries(images))if(m.portrait){count++;assert.ok(m.canonicalFace);const b=api.portraitBox(id,1,0,24);if(m.patch){assert.deepEqual(m.patchRect,[0,0,m.width,m.height]);assert.equal(b.patchLeft,b.left);assert.equal(b.patchTop,b.top);assert.equal(b.patchWidth,b.width);assert.equal(b.patchHeight,b.height);}}
 assert.equal(count,1013);const f=fixture();f.enter(31,6);assert.equal(f.p.speaker,'中年服务生');assert.ok(f.p.bodySrc);assert.equal(f.p.faceWidth,f.p.portraitWidth);assert.equal(f.p.faceHeight,262);
});
test('whole-canvas expression dimensions follow the body during multi-character changes',()=>{
 const f=fixture();for(const [scene,cursor]of [[9,23],[31,0],[31,6],[33,1],[65,18]]){f.enter(scene,cursor);const p=f.p;for(const [face,body]of [['face','portrait'],['faceSecond','portraitSecond'],['faceThird','portraitThird']])if(p[face+'Src']){assert.equal(p[face+'Width'],p[body+'Width']);assert.equal(p[face+'Height'],p[body+'Height']);assert.equal(p[face+'Left'],p[body+'Left']);assert.equal(p[face+'Top'],p[body+'Top']);}}
});
