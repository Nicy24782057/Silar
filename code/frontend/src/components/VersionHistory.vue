<script setup>
import { ref, watch } from 'vue';
import { api, ApiError } from '../api';
import { fieldLabels } from '../analysis';
import { date, label, paginationPath } from '../domain';
import { online } from '../network';
import FetchState from './FetchState.vue';
import EvidenceSources from './EvidenceSources.vue';
const props=defineProps({reportId:{type:String,required:true}});
const versions=ref([]),history=ref([]),nextVersions=ref(null),nextHistory=ref(null);
const busy=ref(false),error=ref(null),selected=ref(null),parent=ref(null),sourceNarrative=ref(null),sourceBundle=ref(null);
const kinds={EvidenceBundle:'Bundle bukti',NarrativeVersion:'Narasi',IncidentCardVersion:'Incident Card',PublicationVersion:'Versi publik'};
const actions={REPORT_CREATED:'Draft dibuat',EVIDENCE_UPLOADED:'Bukti disimpan',BUNDLE_CREATED:'Bundle dipilih',ANALYSIS_PREPARED:'Analisis disiapkan',ANALYSIS_SUCCEEDED:'Analisis selesai',ANALYSIS_FAILED:'Analisis gagal',NARRATIVE_REVISED:'Narasi direvisi',CARD_REVISED:'Kartu direvisi',HUMAN_VERIFIED:'Versi dikonfirmasi Reporter',REPORT_SUBMITTED:'Laporan dikirim'};
const display=value=>Array.isArray(value)?value.length?value.join('; '):'Belum tersedia':value??'Belum tersedia';
async function load(){
  busy.value=true;error.value=null;selected.value=null;parent.value=null;sourceNarrative.value=null;sourceBundle.value=null;
  const id=props.reportId;
  try{
    const [v,h]=await Promise.all([api(`reports/${id}/versions/`),api(`reports/${id}/history/`)]);
    if(id!==props.reportId)return;
    versions.value=v.results;nextVersions.value=v.next;history.value=h.results;nextHistory.value=h.next;
  }catch(e){error.value=e;}finally{busy.value=false;}
}
watch(()=>props.reportId,()=>{versions.value=[];history.value=[];nextVersions.value=null;nextHistory.value=null;load();},{immediate:true});
async function more(kind){
  busy.value=true;error.value=null;
  const id=props.reportId;
  try{
    const result=await api(paginationPath(kind==='versions'?nextVersions.value:nextHistory.value));
    if(id!==props.reportId)return;
    if(kind==='versions'){versions.value=[...versions.value,...result.results];nextVersions.value=result.next;}
    else{history.value=[...history.value,...result.results];nextHistory.value=result.next;}
  }catch(e){error.value=e;}finally{busy.value=false;}
}
async function readVersion(kind,id){
  const result=(await api(`reports/${props.reportId}/versions/${kind}/${id}/`)).data;
  if(result?.kind!==kind||(result.version?.report_id?result.version.report_id!==props.reportId:result.version?.id!==props.reportId))
    throw new ApiError('Referensi versi tidak sesuai laporan. Muat ulang riwayat.','INVALID_RESPONSE');
  return result;
}
async function open(item){
  busy.value=true;error.value=null;parent.value=null;sourceNarrative.value=null;sourceBundle.value=null;
  const id=props.reportId;
  try{const result=await readVersion(item.kind,item.id);if(id===props.reportId)selected.value=result;}
  catch(e){error.value=e;}finally{busy.value=false;}
}
async function compare(){
  busy.value=true;error.value=null;
  const reference=selected.value;
  try{const result=await readVersion(reference.kind,reference.version.parent_id);if(selected.value===reference)parent.value=result;}
  catch(e){error.value=e;}finally{busy.value=false;}
}
async function sources(){
  busy.value=true;error.value=null;
  const reference=selected.value;
  try{
    const values=await Promise.all([readVersion('NarrativeVersion',reference.version.narrative_id),readVersion('EvidenceBundle',reference.version.bundle_id)]);
    if(selected.value===reference){sourceNarrative.value=values[0].version;sourceBundle.value=values[1].version;}
  }catch(e){error.value=e;}finally{busy.value=false;}
}
</script>
<template>
  <section aria-label="Versi dan riwayat laporan">
    <div class="section-heading"><div><h2>Versi dan riwayat</h2><p class="muted">Versi lama tetap dapat dibaca dan tidak menggantikan versi aktif.</p></div><button class="small" :disabled="busy||!online" @click="load">Muat ulang</button></div>
<FetchState v-if="busy" title="Memuat versi dan riwayat…" :caption="'Laporan #'+reportId.slice(0,8)" /><FetchState v-else-if="error" state="error" title="Riwayat belum dapat dimuat" description="Coba lagi untuk membaca versi dan tindakan yang tersimpan." :error="error" :disabled="busy||!online" @retry="load" />
    <div class="info-grid">
      <section class="card"><h2>Daftar versi</h2><p v-if="!versions.length&&!busy&&!error" class="muted">Belum ada versi.</p><ul class="version-list"><li v-for="item in versions" :key="item.kind+item.id"><div><strong>{{ kinds[item.kind] }} · versi {{ item.version_number }}</strong><small>{{ date(item.created_at) }} · {{ item.source_kind==='REPORTER_FIELD_REVISION'||item.source_kind==='REPORTER_REVISION'?'Koreksi Reporter':item.source_kind||'Sumber tersimpan' }}</small><span v-if="item.official" class="badge official-version">Versi resmi</span></div><button class="small" :disabled="busy||!online" :aria-label="'Buka '+kinds[item.kind]+' versi '+item.version_number" @click="open(item)">Buka</button></li></ul><button v-if="nextVersions" class="full" :disabled="busy||!online" @click="more('versions')">Muat versi berikutnya</button></section>
      <section class="card"><h2>Riwayat tindakan</h2><p v-if="!history.length&&!busy&&!error" class="muted">Belum ada tindakan tercatat.</p><ol class="history-list"><li v-for="item in history" :key="item.id"><strong>{{ actions[item.action]||'Keadaan laporan diperbarui' }}</strong><small>{{ date(item.created_at) }} · {{ item.actor_role==='SYSTEM'?'Sistem':item.actor_role }}</small><span v-for="(value,key) in item.states" :key="key" class="badge">{{ label(value) }}</span></li></ol><button v-if="nextHistory" class="full" :disabled="busy||!online" @click="more('history')">Muat tindakan berikutnya</button><p class="fine">Riwayat ini tidak membuka catatan internal petugas.</p></section>
    </div>
    <section v-if="selected" class="card" aria-live="polite"><div class="section-heading"><div><h2>{{ kinds[selected.kind] }} yang dipilih<span v-if="selected.version.version_number"> · versi {{ selected.version.version_number }}</span></h2><p class="muted">{{ date(selected.version.created_at||selected.version.published_at) }}</p></div><button v-if="selected.version.parent_id" class="small" :disabled="busy||!online" @click="compare">Bandingkan dengan induk</button></div>
      <p v-if="selected.kind==='NarrativeVersion'" class="preserve">{{ selected.version.text }}</p>
      <template v-else-if="selected.kind==='IncidentCardVersion'"><h3>{{ label(selected.version.data.event_type) }}</h3><p v-if="selected.version.uncertain" class="notice warning">Versi ini menyimpan penanda ketidakpastian hasil AI.</p><dl class="result-fields"><template v-for="(name,key) in fieldLabels" :key="key"><dt>{{ name }}</dt><dd>{{ display(selected.version.data[key]) }}</dd></template></dl><button :disabled="busy||!online" @click="sources">Baca sumber versi ini</button><p class="fine">Kategori, isi dan sumber mengikuti versi yang dipilih. Skor model dari analisis terbaru tidak digabungkan ke versi lama.</p></template>
      <EvidenceSources v-else-if="selected.kind==='EvidenceBundle'" :bundle="selected.version" title="Isi bundle yang dipilih" />
      <template v-else-if="selected.kind==='PublicationVersion'"><dl class="result-fields"><template v-for="(value,key) in (selected.version.data||selected.version)" :key="key"><dt>{{ key }}</dt><dd>{{ display(value) }}</dd></template></dl></template>
      <section v-if="parent" class="version-comparison"><h3>Perbandingan dengan versi induk {{ parent.version.version_number }}</h3><div v-if="selected.kind==='NarrativeVersion'" class="info-grid"><div><strong>Induk</strong><p class="preserve">{{ parent.version.text }}</p></div><div><strong>Versi dipilih</strong><p class="preserve">{{ selected.version.text }}</p></div></div><dl v-else-if="selected.kind==='IncidentCardVersion'" class="result-fields"><template v-for="(name,key) in fieldLabels" :key="key"><template v-if="JSON.stringify(parent.version.data[key])!==JSON.stringify(selected.version.data[key])"><dt>{{ name }}</dt><dd><div>Induk: {{ display(parent.version.data[key]) }}</div><div>Versi dipilih: {{ display(selected.version.data[key]) }}</div></dd></template></template></dl><p v-else class="fine">Baca isi versi induk melalui daftar versi sesuai hak akses.</p></section>
      <section v-if="sourceNarrative"><h3>Narasi sumber versi ini</h3><p class="preserve">{{ sourceNarrative.text }}</p></section><EvidenceSources v-if="sourceBundle" :bundle="sourceBundle" title="Bukti sumber versi ini" />
    </section>
  </section>
</template>
