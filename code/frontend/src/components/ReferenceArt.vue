<script setup>
import { computed } from 'vue';
import { theme } from '../theme';
const props = defineProps({source:{type:String,required:true},darkSource:String, alt:{type:String,default:''}});
const url = computed(() => theme.mode==='dark'&&props.darkSource?props.darkSource:props.source);
</script>
<template><img :src="url" :alt="alt" class="reference-art"></template>
