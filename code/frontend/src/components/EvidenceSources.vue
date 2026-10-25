<script setup>
import { onBeforeUnmount, ref, watch } from 'vue';
import { api } from '../api';
import { online } from '../network';
import { date, size } from '../domain';
import ErrorNotice from './ErrorNotice.vue';
import AppIcon from './AppIcon.vue';
const props=defineProps({bundle:Object,title:{type:String,default:'Bukti sumber'}});
const previews=ref({}),error=ref(null),busy=ref(null);
let alive=true;
function release(){for(const value of Object.values(previews.value))URL.revokeObjectURL(value);previews.value={};}
watch(()=>props.bundle?.id,()=>{release();error.value=null;});
onBeforeUnmount(()=>{alive=false;release();});
async function show(item){
  if(previews.value[item.id])return;
  busy.value=item.id;error.value=null;
  const source=props.bundle?.id;
  try{
    const blob=await api(`evidence/${item.id}/media/`,{raw:true});
    if(alive&&source===props.bundle?.id)previews.value={...previews.value,[item.id]:URL.createObjectURL(blob)};
  }catch(e){error.value=e;}finally{busy.value=null;}
}
</script>
<template>
  <section class="card sources-readonly">
    <div class="section-heading"><div class="title-with-icon"><span class="heading-icon"><AppIcon name="image" :size="18" /></span><div><h2>{{ title }}</h2><p v-if="bundle" class="muted">Sumber versi {{ bundle.version_number }} · {{ bundle.items.length }} bukti</p></div></div><span class="badge private-badge"><AppIcon name="lock" :size="12" /> Privat</span></div>
    <ErrorNotice :error="error" />
    <p v-if="!bundle" class="muted">Sumber belum tersedia untuk diperiksa.</p>
    <ul v-else class="evidence-list"><li v-for="entry in bundle.items" :key="entry.evidence.id" class="evidence-item">
      <div class="evidence-top"><strong>{{ entry.evidence.type==='TEXT'?'Keterangan asli':entry.evidence.original_name }}</strong><span class="channel-tag">{{ entry.evidence.type }}</span></div>
      <p v-if="entry.evidence.type==='TEXT'" class="evidence-text">{{ entry.evidence.text_content }}</p>
      <div class="evidence-meta">{{ size(entry.evidence.byte_size) }} · {{ date(entry.evidence.created_at) }}</div>
      <template v-if="entry.evidence.type!=='TEXT'"><button class="link" :disabled="!online||busy===entry.evidence.id" @click="show(entry.evidence)">{{ previews[entry.evidence.id]?'Media telah dibuka':entry.evidence.type==='IMAGE'?'Buka gambar privat':'Dengarkan audio privat' }}</button><img v-if="previews[entry.evidence.id]&&entry.evidence.type==='IMAGE'" class="evidence-image" :src="previews[entry.evidence.id]" :alt="'Bukti: '+entry.evidence.original_name"><audio v-if="previews[entry.evidence.id]&&entry.evidence.type==='AUDIO'" :src="previews[entry.evidence.id]" controls preload="metadata" :aria-label="'Bukti: '+entry.evidence.original_name"></audio></template>
    </li></ul>
    <p class="fine">Bukti asli tetap disimpan. Informasi yang tidak tersedia tidak otomatis berarti tidak ada.</p>
  </section>
</template>
