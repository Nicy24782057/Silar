<script setup>
import {ref} from 'vue';
defineProps({viewKey:{type:String,required:true},label:String});
const heldHeight=ref(null);
function hold(element){heldHeight.value=element.getBoundingClientRect().height+'px';element.inert=true;}
function entered(element){
  heldHeight.value=null;
  const heading=element.querySelector('[data-process-heading],h2,h3');
  if(!heading)return;
  heading.tabIndex=-1;heading.focus({preventScroll:true});
  const box=heading.getBoundingClientRect();
  if(box.top<12||box.top>innerHeight-100)heading.scrollIntoView({block:'start',
    behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});
}
</script>
<template>
 <div class="process-outlet" :style="{minHeight:heldHeight}" :aria-label="label">
  <Transition name="process-change" mode="out-in" @before-leave="hold" @after-enter="entered" @leave-cancelled="el=>{heldHeight=null;el.inert=false}">
   <div :key="viewKey" class="process-content"><slot /></div>
  </Transition>
 </div>
</template>
