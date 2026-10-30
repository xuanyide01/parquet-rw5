export function groupGallery(items){const groups=[],by={};for(const item of items){const id=item.group||item.source;let g=by[id];if(!g){g={id,image:item.image,label:item.label,variants:[]};by[id]=g;groups.push(g);}g.variants.push(item);}return groups;}
export function stepVariant(index,delta,count){return count?((index+delta)%count+count)%count:0;}
