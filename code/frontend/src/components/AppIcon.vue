<script setup>
import { computed } from 'vue';
const props=defineProps({name:{type:String,default:'file'},size:{type:[Number,String],default:20}});
const paths={
  file:['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z','M14 2v6h6','M8 13h8M8 17h5'],
  folder:['M3 5h6l2 3h10v12H3Z'],
  reports:['M8 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z','M3 6v12M11 8h6M11 12h6M11 16h4'],
  plus:['M12 5v14M5 12h14'],
  bell:['M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9','M10 21h4'],
  user:['M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z','M4 21v-2a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v2'],
  device:['M7 2h10a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z','M10 18h4'],
  shield:['M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6Z','m8 12 3 3 5-6'],
  arrow:['M5 12h14m-6-6 6 6-6 6'],
  left:['M19 12H5m6-6-6 6 6 6'],
  chevron:['m9 5 7 7-7 7'],
  down:['m6 9 6 6 6-6'],
  check:['m5 12 4 4L19 6'],
  clock:['M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z','M12 6v6l4 2'],
  refresh:['M20 7a9 9 0 1 0 1 9','M20 2v6h-6'],
  moon:['M21 13a9 9 0 1 1-10-10 7 7 0 0 0 10 10Z'],
  sun:['M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z','M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1 1M18 18l1 1M5 19l1-1M18 6l1-1'],
  logout:['M9 3H4v18h5','M12 12h9m-4-4 4 4-4 4'],
  menu:['M4 6h16M4 12h16M4 18h16'],
  close:['m6 6 12 12M6 18 18 6'],
  edit:['m16 3 5 5-12 12-6 1 1-6Z','m13 6 5 5'],
  send:['m22 2-7 20-4-9-9-4Z','M22 2 11 13'],
  info:['M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z','M12 11v6M12 7h.01'],
  lock:['M6 10h12a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1Z','M8 10V6a4 4 0 0 1 8 0v4M12 14v3'],
  waves:['M2 7c3-4 7 4 10 0s7 4 10 0M2 12c3-4 7 4 10 0s7 4 10 0M2 17c3-4 7 4 10 0s7 4 10 0'],
  flame:['M12 2c1 6 7 6 7 13a7 7 0 0 1-14 0c0-4 2-5 3-8 0 3 2 4 3 4 2-2 2-6 1-9Z'],
  pulse:['M2 12h5l3-8 4 16 3-8h5'],
  car:['m5 5-3 7v7h3v-3h14v3h3v-7l-3-7Z','M2 12h20M6 12V9h12v3M6 15h.01M18 15h.01'],
  image:['M4 3h16a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z','m3 16 6-6 5 5 3-3 4 4M16 7h.01'],
  audio:['M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z','M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8'],
  history:['M3 12a9 9 0 1 0 3-7','M3 2v6h6M12 7v5l3 2'],
  search:['M21 21l-5-5','M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z'],
  wrench:['M14.7 6.3a5 5 0 0 0-6.4 6.4L2 19l3 3 6.3-6.3a5 5 0 0 0 6.4-6.4L14 13l-3-3Z'],
  alert:['M10.3 3.9 1.8 18.5A2 2 0 0 0 3.5 21h17a2 2 0 0 0 1.7-2.5L13.7 3.9a2 2 0 0 0-3.4 0Z','M12 9v4M12 17h.01'],
  'circle-check':['M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z','m7 12 3 3 7-7'],
};
const strokes=computed(()=>paths[props.name]||paths.file);
</script>
<template><svg class="app-icon" :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path v-for="(d,i) in strokes" :key="i" :d="d" /></svg></template>
