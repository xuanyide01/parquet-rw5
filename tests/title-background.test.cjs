const {test}=require('node:test'),assert=require('node:assert/strict');
const {api,fixture}=require('./fixture.cjs');
const settings='parquet_rw5_settings_v1',progress=api.PROGRESS_KEY;
function values(vars,index){return {[progress]:JSON.stringify({version:1,variables:vars}),[settings]:JSON.stringify({fontSize:28,textSpeed:0,autoSpeed:2,titleBackgroundIndex:index})};}
test('original three-background rules: main clear alone does not unlock either ending image',()=>{
 assert.deepEqual(api.titleBackgroundDefinitions.map(x=>x.file),['title_bg','title_bg_rin','title_bg_tsu']);
 for(const [vars,status]of [[{},[true,false,false]],[{'sf.parquet_main_clear':true},[true,false,false]],[{'sf.parquet_after_rin_clear':true},[true,true,false]],[{'sf.parquet_after_tsu_clear':true},[true,false,true]],[{'sf.parquet_after_rin_clear':true,'sf.parquet_after_tsu_clear':true},[true,true,true]]])assert.deepEqual(api.titleBackgroundStatus(vars).map(x=>x.unlocked),status);
});
test('locked backgrounds conceal their thumbnails and cannot be selected or persisted',()=>{
 const {p,writes}=fixture(values({'sf.parquet_main_clear':true},0));p.openSettings();const before=writes.length;assert.equal(p.titleBackgroundRows[1].thumbnailSrc,'/common/ui/title-locked.png');p.selectTitleBackground(1);assert.equal(writes.length,before);assert.equal(p.titleBackgroundIndex,0);assert.match(p.titleBackgroundHint,/梨乃/);assert.equal(p.titleBackgroundSrc,'/common/ui/title-0.jpg');
});
test('unlocked selections persist through app restart and entering/leaving actual gameplay',()=>{
 for(const index of [0,1,2]){
  const vars={'sf.parquet_side_clear':true,'sf.parquet_main_clear':true,'sf.parquet_after_rin_clear':true,'sf.parquet_after_tsu_clear':true};const f=fixture(values(vars,0));const {p,data,clock}=f;p.openSettings();p.selectTitleBackground(index);assert.equal(p.titleBackgroundSrc,'/common/ui/title-'+index+'.jpg');assert.equal(p.titleBackgroundRows[index].stateLabel,'使用中');p.closeSettings();p.startNew();clock.tick(0);p.toTitle();assert.equal(p.titleBackgroundSrc,'/common/ui/title-'+index+'.jpg');
  const saved=JSON.parse(data.get(settings));assert.equal(saved.titleBackgroundIndex,index);assert.equal(saved.fontSize,28);assert.equal(saved.autoSpeed,2);const restarted=fixture(Object.fromEntries(data));assert.equal(restarted.p.titleBackgroundSrc,p.titleBackgroundSrc);assert.equal(restarted.p.afterUnlocked,true);assert.equal(restarted.p.autoEnabled,false);
 }
});
test('old v0.1.0 settings migrate to default; invalid or locked persisted selections render default safely',()=>{
 for(const index of [undefined,null,-1,3,'1',NaN,999,1,2]){const {p}=fixture(values({},index));assert.equal(p.titleBackgroundSrc,'/common/ui/title-0.jpg');}
 const {p}=fixture({[settings]:JSON.stringify({fontSize:28,textSpeed:0,autoSpeed:2})});assert.equal(p.fontSize,28);assert.equal(p.autoSpeed,2);assert.equal(p.titleBackgroundIndex,0);
});
test('only the matching normally completed AFTER STORY unlocks its image; chapter preview cannot unlock',()=>{
 const {p}=fixture();p.textSpeed=0;
 for(const [id,flag,index]of [[103,'sf.parquet_after_rin_clear',1],[107,'sf.parquet_after_tsu_clear',2]]){
  p.session=api.newState(id,false);p.cachedChapter=0;p.renderFrame();assert.equal(p.titleBackgroundRows[index].unlocked,false);
  p.session=api.newState(id,true);p.cachedChapter=0;p.renderFrame();assert.equal(p._progress.variables[flag],true);assert.equal(p.titleBackgroundRows[index].unlocked,true);assert.equal(p.titleBackgroundIndex,index);
 }
});
test('System from the reading grid pauses autoplay and returns to the same menu/cursor',()=>{
 const f=fixture(),{p,clock}=f;f.enter();f.enable();p.showMenu();const cursor=p.session.cursor;p.openSettings();assert.equal(p.mode,'settings');assert.equal(p.settingsReturnLabel,'返回菜单');clock.tick(100000);assert.equal(p.session.cursor,cursor);p.closeSettings();assert.equal(p.mode,'menu');assert.equal(p.autoEnabled,true);clock.tick(100000);assert.equal(p.session.cursor,cursor);p.resume();clock.tick(api.autoWait(1,p.fullText.length));assert.equal(p.session.cursor,cursor+1);
});

test('completion switches the matching background again on replay and manual choices remain after restart',()=>{
 const f=fixture(),{p,data}=f;for(const [id,index]of [[103,1],[107,2],[103,1]]){p.session=api.newState(id,true);p.cachedChapter=0;p.renderFrame();assert.equal(p.mode,'title');assert.equal(p.titleBackgroundIndex,index);assert.equal(JSON.parse(data.get(settings)).titleBackgroundIndex,index);}
 p.selectTitleBackground(0);assert.equal(fixture(Object.fromEntries(data)).p.titleBackgroundIndex,0);
});
test('background cards recreate selected rows immediately and feedback identifies the selected image',()=>{
 const f=fixture(values({'sf.parquet_after_rin_clear':true,'sf.parquet_after_tsu_clear':true},0)),{p}=f;p.openSettings();const first=p.titleBackgroundRows.map(r=>r.key);
 p.selectTitleBackground(1);assert.deepEqual(Array.from(p.titleBackgroundRows,r=>r.selected),[false,true,false]);assert.notEqual(p.titleBackgroundRows[0].key,first[0]);assert.notEqual(p.titleBackgroundRows[1].key,first[1]);assert.equal(p.titleBackgroundHint,'当前：梨乃背景');
 p.selectTitleBackground(2);assert.deepEqual(Array.from(p.titleBackgroundRows,r=>r.selected),[false,false,true]);assert.equal(p.titleBackgroundHint,'当前：翼背景');
});
