// default.tjs GetTitleImageFile.Status: default=true, rin=after.rin, tsu=after.tsu.
export const titleBackgroundDefinitions=[
 {index:0,label:'默认',file:'title_bg',source:'/common/ui/title-0.jpg',thumbnail:'/common/ui/title-thumb-0.jpg',flag:'',requirement:'默认背景始终可用'},
 {index:1,label:'梨乃',file:'title_bg_rin',source:'/common/ui/title-1.jpg',thumbnail:'/common/ui/title-thumb-1.jpg',flag:'sf.parquet_after_rin_clear',requirement:'完成梨乃的后日谈后解锁'},
 {index:2,label:'翼',file:'title_bg_tsu',source:'/common/ui/title-2.jpg',thumbnail:'/common/ui/title-thumb-2.jpg',flag:'sf.parquet_after_tsu_clear',requirement:'完成翼的后日谈后解锁'}
];
export function titleBackgroundStatus(variables){const v=variables||{};return titleBackgroundDefinitions.map(d=>Object.assign({},d,{unlocked:!d.flag||!!v[d.flag]}));}
export function resolveTitleBackground(index,variables){const n=Number.isInteger(index)&&index>=0&&index<3?index:0,rows=titleBackgroundStatus(variables);return rows[n].unlocked?n:0;}
