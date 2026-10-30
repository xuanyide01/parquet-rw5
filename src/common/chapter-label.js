import {catalog} from './catalog.js';
export function chapterLabel(state){return catalog.chapterLabels[state.chapterTag]||catalog.scenes[String(state.rootChapter)].name;}
