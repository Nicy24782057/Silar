<script setup>
import { useRoute } from 'vue-router';
import {ref} from 'vue';
const route=useRoute();
const heldHeight=ref(null);
function hold(element){heldHeight.value=element.getBoundingClientRect().height+'px';}
</script>
<template>
 <div class="route-outlet" :style="{minHeight:heldHeight}"><RouterView v-slot="{Component}"><Transition name="page-change" mode="out-in" @before-leave="hold" @after-enter="heldHeight=null" @leave-cancelled="heldHeight=null"><div v-if="Component" :key="route.path" class="route-page"><component :is="Component" /></div></Transition></RouterView></div>
</template>
