const {test}=require('node:test'),assert=require('node:assert/strict');
const {api,fixture}=require('./fixture.cjs');
test('menu pauses auto, three speeds wait after text, and new sentences type at 30 ms',()=>{
 assert.deepEqual([0,1,2].map(i=>api.autoWait(i,40)),[2600,1500,800]);const f=fixture(),{p,clock}=f;f.enter();p.showMenu();p.toggleAuto();clock.tick(10000);assert.equal(p.session.cursor,0);p.resume();clock.tick(1499);assert.equal(p.session.cursor,0);clock.tick(1);assert.equal(p.session.cursor,1);assert.equal(p.displayText.length,1);clock.tick(30);assert.equal(p.displayText.length,2);f.typed();
 const pos=p.session.cursor;clock.tick(api.autoWait(p.autoSpeed,p.fullText.length));assert.equal(p.session.cursor,pos+1);
});
test('actual after-story choice waits indefinitely, then resumes on the selected branch',()=>{
 const f=fixture(),{p,clock}=f;f.enter(95,api.catalog.scenes[95].length-2);f.enable();clock.tick(api.autoWait(1,p.fullText.length));assert.equal(p.mode,'choice');assert.equal(p.session.chapter,98);clock.tick(100000);assert.equal(p.session.choices.length,0);assert.equal(p._autoTimer,null);assert.equal(p.autoEnabled,true);
 p.pick(1);clock.tick(0);assert.equal(p.mode,'play');assert.equal(p.session.chapter,104);assert.equal(p.session.variables['s015*chapter7_sel1'],2);f.typed();const pos=p.session.cursor;clock.tick(api.autoWait(1,p.fullText.length));assert.equal(p.session.cursor,pos+1);
});
test('background/menu/scroll pause, stale callbacks cannot advance, and fresh tap still advances',()=>{
 const f=fixture(),{p,clock}=f;f.enter();f.enable();const stale=clock.tasks.get(p._autoTimer).fn;p.onHide();stale();clock.tick(100000);assert.equal(p.session.cursor,0);p.onShow();clock.tick(1499);assert.equal(p.session.cursor,0);
 p.dialogueTouchStart({touches:[{pageX:200,pageY:430}]});clock.tick(100000);assert.equal(p.session.cursor,0);p.dialogueTouchMove({touches:[{pageX:200,pageY:330}]});p.dialogueTouchEnd();p.dialogueTap();assert.equal(p.session.cursor,0);p.dialogueScrolled({scrollY:35});clock.tick(1499);assert.equal(p.session.cursor,0);
 p.dialogueTouchStart({touches:[{pageX:200,pageY:370}]});p.dialogueTouchEnd();p.dialogueTap();assert.equal(p.session.cursor,1);p.goBack();assert.equal(p.autoEnabled,false);
});
test('save/load pages pause autoplay and restore a real pending choice in slot 30',()=>{
 const saved=api.createSave(api.newState(98,true),'choice',1000),f=fixture({[api.slotKey(29)]:JSON.stringify(saved)}),{p,clock}=f;f.enter();f.enable();p.showMenu();p.loadGame();clock.tick(0);assert.equal(p.mode,'slots');clock.tick(100000);assert.equal(p.session.cursor,0);p.selectSlot(29);clock.tick(0);assert.equal(p.mode,'choice');clock.tick(100000);assert.equal(p.session.chapter,98);p.pick(0);clock.tick(0);assert.equal(p.mode,'play');assert.equal(p.session.chapter,100);
});
test('speed persists but automatic playback is off at every restart; title/end/error/exit cancel timers',()=>{
 const f=fixture(),{p,data,clock}=f;f.enter();f.enable();p.cycleAutoSpeed();assert.equal(p.autoSpeed,2);const raw=data.get('parquet_rw5_settings_v1');assert.ok(!('autoEnabled'in JSON.parse(raw)));const restart=fixture({'parquet_rw5_settings_v1':raw});assert.equal(restart.p.autoSpeed,2);assert.equal(restart.p.autoEnabled,false);
 for(const action of ['title','end','error','exit']){f.enter();f.enable();if(action==='title')p.toTitle();else if(action==='end'){p.session=api.newState(107,true);p.cachedChapter=0;p.renderFrame();}else if(action==='error')p.fail('test');else p.exitApplication();const pos=[p.session.chapter,p.session.cursor];clock.tick(100000);assert.equal(p.autoEnabled,false);assert.equal(p._autoTimer,null);assert.deepEqual([p.session.chapter,p.session.cursor],pos);}
});
test('canceled pending reads cannot resurrect a game behind title',()=>{
 const f=fixture(),{p}=f;f.enter();f.defer();p.session=api.newState(3,true);p.cachedChapter=0;p.renderFrame();assert.equal(p._needsFrame,true);p.toTitle();p.onHide();p.onShow();f.flush();assert.equal(p.mode,'title');assert.equal(p._needsFrame,false);
});
