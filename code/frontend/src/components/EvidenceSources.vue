<script setup>
import { onBeforeUnmount, ref, watch } from 'vue';
import { api } from '../api';
import { online } from '../network';
import { date, size } from '../domain';
import ErrorNotice from './ErrorNotice.vue';
import AppIcon from './AppIcon.vue';
import FetchState from './FetchState.vue';
const props=defineProps({bundle:Object,title:{type:String,default:'Bukti sumber'},comparison:Boolean,narrative:Object});
const tab=ref('evidence');
const previews=ref({}),error=ref(null),busy=ref(null);
let alive=true;
function release(){for(const value of Object.values(previews.value))URL.revokeObjectURL(value);previews.value={};}
watch(()=>props.bundle?.id,()=>{release();error.value=null;busy.value=null;});
onBeforeUnmount(()=>{alive=false;release();});
async function show(item){
  if(previews.value[item.id])return;
  busy.value=item.id;error.value=null;
  const source=props.bundle?.id;
  try{
    const blob=await api(`evidence/${item.id}/media/`,{raw:true});
    if(alive&&source===props.bundle?.id)previews.value={...previews.value,[item.id]:URL.createObjectURL(blob)};
  }catch(e){if(alive&&source===props.bundle?.id)error.value=e;}finally{if(alive&&source===props.bundle?.id)busy.value=null;}
}
</script>
<template>
  <section class="card sources-readonly">
    <div class="section-heading" :class="{'compose-panel-heading':comparison}"><div class="title-with-icon"><span class="heading-icon"><AppIcon :name="comparison?'search':'image'" :size="18" /></span><div><h2>{{ title }}</h2><p v-if="comparison" class="muted">Bukti asli tetap privat dan utuh.</p><p v-else-if="bundle" class="muted">Sumber versi {{ bundle.version_number }} · {{ bundle.items.length }} bukti</p></div></div><span v-if="!comparison" class="badge private-badge"><AppIcon name="lock" :size="12" /> Privat</span></div>
    <div :class="{'compose-panel-body':comparison}">
    <div v-if="comparison&&narrative" class="compose-tabs" role="tablist" aria-label="Sumber pembanding"><button role="tab" :aria-selected="tab==='evidence'" @click="tab='evidence'">Bukti</button><button role="tab" :aria-selected="tab==='narrative'" @click="tab='narrative'">Narasi</button></div>
    <ErrorNotice :error="error" />
    <FetchState v-if="!bundle" state="empty" compact title="Sumber belum tersedia" description="Sumber untuk versi ini belum tersedia untuk diperiksa." />
    <ul v-else v-show="!comparison||!narrative||tab==='evidence'" class="evidence-list"><li v-for="entry in bundle.items" :key="entry.evidence.id" class="evidence-item">
      <div class="evidence-top"><AppIcon v-if="comparison" :name="entry.evidence.type==='TEXT'?'file':entry.evidence.type==='AUDIO'?'audio':'image'" :size="18" /><strong>{{ entry.evidence.type==='TEXT'?'Teks asli':entry.evidence.original_name }}</strong><span :class="comparison?'badge':'channel-tag'">{{ comparison?'Privat':entry.evidence.type }}</span></div>
      <p v-if="entry.evidence.type==='TEXT'" class="evidence-text">{{ entry.evidence.text_content }}</p>
      <div class="evidence-meta">{{ size(entry.evidence.byte_size) }} · {{ date(entry.evidence.created_at) }}</div>
      <template v-if="entry.evidence.type!=='TEXT'"><button class="link" :disabled="!online||busy===entry.evidence.id" @click="show(entry.evidence)">{{ previews[entry.evidence.id]?'Media telah dibuka':entry.evidence.type==='IMAGE'?'Buka gambar privat':'Dengarkan audio privat' }}</button><img v-if="previews[entry.evidence.id]&&entry.evidence.type==='IMAGE'" class="evidence-image" :src="previews[entry.evidence.id]" :alt="'Bukti: '+entry.evidence.original_name"><audio v-if="previews[entry.evidence.id]&&entry.evidence.type==='AUDIO'" :src="previews[entry.evidence.id]" controls preload="metadata" :aria-label="'Bukti: '+entry.evidence.original_name"></audio></template>
    </li></ul>
    <section v-if="comparison&&narrative" v-show="tab==='narrative'" class="source-narrative"><h3>Narasi aktif <span class="badge">v{{ narrative.version_number }}</span></h3><p class="fine">{{ narrative.origin==='REPORTER_REVISION'?'Revisi Reporter':'Hasil pembentukan narasi' }}</p><p class="preserve narrative-copy" tabindex="0" role="region" aria-label="Isi narasi aktif">{{ narrative.text }}</p><slot name="narrative-actions" /></section>
    <p class="fine">Bukti asli tetap disimpan. Informasi yang tidak tersedia tidak otomatis berarti tidak ada.</p>
    </div>
  </section>
</template>
