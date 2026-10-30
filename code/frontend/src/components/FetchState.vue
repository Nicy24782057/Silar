<script setup>
import { computed } from 'vue';
import AppIcon from './AppIcon.vue';
const props=defineProps({
  state:{type:String,default:'loading'},title:{type:String,required:true},description:String,
  caption:String,compact:Boolean,disabled:Boolean,error:Object,icon:String,retryLabel:{type:String,default:'Coba lagi'},
});
defineEmits(['retry']);
const loading=computed(()=>props.state==='loading');
const heading=computed(()=>loading.value?'Memuat data':props.state==='error'?'Gagal memuat':'Data belum tersedia');
const icon=computed(()=>props.icon||(loading.value?'refresh':props.state==='error'?'globe':'reports'));
</script>
<template>
  <section class="fetch-state" :class="[state,{'fetch-state-compact':compact}]" :aria-busy="loading" :role="state==='error'?'alert':'status'" aria-live="polite">
    <header v-if="!compact" class="fetch-state-heading"><h2>{{ heading }}</h2><p v-if="caption">{{ caption }}</p></header>
    <div class="fetch-state-body">
      <AppIcon :name="icon" :size="25" class="fetch-state-icon" :class="{'is-spinning':loading}" />
      <div class="fetch-state-copy"><h3>{{ title }}</h3><p v-if="description">{{ description }}</p>
        <div v-if="loading" class="fetch-skeleton" aria-hidden="true"><i></i><i></i><i></i></div>
        <p v-if="error?.retryAfter" class="fetch-state-note">Tunggu {{ error.retryAfter }} detik sebelum mencoba kembali.</p>
        <small v-if="error?.requestId">ID bantuan: {{ error.requestId }}</small>
      </div>
      <span v-if="loading" class="fetch-state-waiting">Menunggu respons</span>
      <button v-else-if="state==='error'" :disabled="disabled" @click="$emit('retry')"><AppIcon name="refresh" :size="15" />{{ retryLabel }}</button>
      <slot name="actions" />
    </div>
  </section>
</template>
