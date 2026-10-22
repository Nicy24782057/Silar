<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api, ApiError } from '../api';
import { online } from '../network';
import { validateText, validateFile, validateBundle, usesGemini, paginationPath, label, date, size, textLength } from '../domain';
import ErrorNotice from '../components/ErrorNotice.vue';
import AudioRecorder from '../components/AudioRecorder.vue';
import AnalysisResult from '../components/AnalysisResult.vue';
const route=useRoute();const router=useRouter();
const detail=ref(null);const evidence=ref([]);const count=ref(0);const next=ref(null);const selected=ref([]);
const text=ref('');const audio=ref(null);const images=ref([]);const preview=ref({});
const busy=ref(false);const loading=ref(false);const analysing=ref(false);const error=ref(null);const message=ref('');
const unknown=ref(false);const consent=ref(false);const requestRows=ref([]);
const isNew=computed(()=>route.params.id==='new');
const report=computed(()=>detail.value?.report);
const active=computed(()=>detail.value?.active_bundle);
const editable=computed(()=>report.value?.workflow_status==='NOT_SUBMITTED');
const held=computed(()=>['RUNNING','UNKNOWN'].includes(detail.value?.latest_run?.status));
const locked=computed(()=>busy.value||loading.value||analysing.value||unknown.value||!online.value);
const selectedItems=computed(()=>{const known=new Map(evidence.value.map(x=>[x.id,x]));for(const x of active.value?.items||[])known.set(x.evidence.id,x.evidence);return selected.value.map(id=>known.get(id)).filter(Boolean);});
const selectionSaved=computed(()=>{const ids=active.value?.items.map(x=>x.evidence.id)||[];return ids.length===selected.value.length&&ids.every((id,i)=>id===selected.value[i]);});
const external=computed(()=>usesGemini((active.value?.items||[]).map(x=>x.evidence)));
const audioUrl=ref(null);
watch(audio, value=>{if(audioUrl.value)URL.revokeObjectURL(audioUrl.value);audioUrl.value=value?URL.createObjectURL(value):null;});
function releasePreviews(){for(const value of Object.values(preview.value))URL.revokeObjectURL(value);preview.value={};}
onBeforeUnmount(()=>{releasePreviews();if(audioUrl.value)URL.revokeObjectURL(audioUrl.value);});
function addEvidence(rows){const known=new Map(evidence.value.map(x=>[x.id,x]));for(const item of rows)known.set(item.id,item);evidence.value=Array.from(known.values());}
async function load(){
  error.value=null;loading.value=true;requestRows.value=[];releasePreviews();consent.value=false;
  try{
    if(isNew.value){detail.value=null;evidence.value=[];selected.value=[];return;}
    detail.value=(await api('reports/'+route.params.id+'/')).data;
    selected.value=(detail.value.active_bundle?.items||[]).map(x=>x.evidence.id);
    evidence.value=[];count.value=0;next.value=null;
    if(editable.value){const result=await api('reports/'+route.params.id+'/evidence/');evidence.value=result.results;count.value=result.count;next.value=result.next;}
    else{evidence.value=(detail.value.official_bundle?.items||detail.value.active_bundle?.items||[]).map(x=>x.evidence);count.value=evidence.value.length;}
    unknown.value=false;
  }catch(e){error.value=e;}finally{loading.value=false;}
}
watch(()=>route.params.id,()=>{text.value='';audio.value=null;images.value=[];message.value='';load();},{immediate:true});
async function create(){busy.value=true;error.value=null;try{const result=await api('reports/',{method:'POST',body:{},key:crypto.randomUUID()});await router.replace('/reports/'+result.data.report.id);}catch(e){fail(e);}finally{busy.value=false;}}
function fail(e){error.value=e;if(e.code==='RESPONSE_UNKNOWN')unknown.value=true;}
async function more(){loading.value=true;error.value=null;try{const result=await api(paginationPath(next.value));addEvidence(result.results);count.value=result.count;next.value=result.next;}catch(e){fail(e);}finally{loading.value=false;}}
async function upload(kind,value){
  const problem=kind==='TEXT'?validateText(value):validateFile(value,kind);
  if(problem)throw new ApiError(problem,'INVALID_PAYLOAD');
  if(kind==='IMAGE'&&window.createImageBitmap){let bitmap;try{bitmap=await createImageBitmap(value);if(bitmap.width*bitmap.height>12_000_000)throw new ApiError('Gambar maksimal 12 megapiksel.','INVALID_PAYLOAD');}finally{bitmap?.close();}}
  const body=new FormData();body.append('type',kind);body.append('expected_revision',String(report.value.revision));
  body.append(kind==='TEXT'?'text_content':'file',value);
  const result=await api('reports/'+report.value.id+'/evidence/',{method:'POST',body,key:crypto.randomUUID()});
  detail.value.report=result.data.report;addEvidence([result.data.object]);count.value++;message.value='Bukti tersimpan privat. Pilih bukti di panel untuk membentuk bundle.';
}
async function saveText(){busy.value=true;error.value=null;message.value='';try{await upload('TEXT',text.value);text.value='';}catch(e){fail(e);}finally{busy.value=false;}}
async function saveAudio(){busy.value=true;error.value=null;message.value='';try{await upload('AUDIO',audio.value);audio.value=null;}catch(e){fail(e);}finally{busy.value=false;}}
async function saveImages(event){busy.value=true;error.value=null;message.value='';try{if(!images.value.length)throw new ApiError('Pilih gambar terlebih dahulu.','INVALID_PAYLOAD');for(const file of images.value)await upload('IMAGE',file);}catch(e){fail(e);}finally{busy.value=false;images.value=[];event.target.reset();}}
async function bundle(){
  error.value=null;message.value='';const problem=validateBundle(selectedItems.value);
  if(problem){error.value=new ApiError(problem,'INVALID_PAYLOAD');return;}
  busy.value=true;
  try{await api('reports/'+report.value.id+'/bundles/',{method:'POST',body:{evidence_ids:selected.value,expected_revision:report.value.revision},key:crypto.randomUUID()});await load();message.value='Bundle tersimpan. Sumber analisis mengikuti pilihan bukti pada versi ini.';}
  catch(e){fail(e);}finally{busy.value=false;}
}
async function showMedia(item){
  error.value=null;if(preview.value[item.id])return;
  try{const blob=await api('evidence/'+item.id+'/media/',{raw:true});preview.value={...preview.value,[item.id]:URL.createObjectURL(blob)};}
  catch(e){fail(e);}
}
async function analyse(){
  error.value=null;message.value='';
  if(text.value.trim()||audio.value||images.value.length){error.value=new ApiError('Masih ada input yang belum disimpan. Simpan bukti atau kosongkan input sebelum analisis.','INVALID_PAYLOAD');return;}
  if(!active.value||!selectionSaved.value){error.value=new ApiError('Simpan pilihan bukti menjadi bundle terlebih dahulu.','INVALID_PAYLOAD');return;}
  if(external.value&&!consent.value){error.value=new ApiError('Baca informasi pemrosesan eksternal dan centang pernyataan sebelum melanjutkan.','INVALID_PAYLOAD');return;}
  analysing.value=true;
  try{
    await api('reports/'+report.value.id+'/analyses/',{method:'POST',key:crypto.randomUUID(),body:{mode:'EVIDENCE',bundle_id:active.value.id,input_revision:report.value.input_revision,expected_revision:report.value.revision}});
    await load();message.value='Hasil analisis sudah dibaca kembali dari server. Laporan belum dikirim resmi.';
  }catch(e){if(e.status===404||e.status===405)e=new ApiError('Layanan analisis belum tersedia. Bukti dan bundle tetap tersimpan; coba kembali setelah layanan siap.','AI_CONFIGURATION_NOT_READY',503);fail(e);}
  finally{analysing.value=false;}
}
async function checkRequests(){
  loading.value=true;error.value=null;
  try{await load();const result=await api('requests/?report_id='+route.params.id);requestRows.value=result.results;
    if(!requestRows.value.length)message.value='Tidak ada request analisis pada halaman ini. Periksa sumber dan hasil tersimpan sebelum tindakan baru.';
  }catch(e){if(e.status===404)e=new ApiError('Pembacaan request analisis belum tersedia. Bukti dapat diperiksa melalui daftar sumber tersimpan.','AI_CONFIGURATION_NOT_READY',503);fail(e);}finally{loading.value=false;}
}
</script>
<template>
  <div class="page-heading"><div><div class="eyebrow">LAPORAN PRIVAT</div><h1>{{ isNew?'Buat laporan':'Draft & bukti laporan' }}</h1><p class="subtitle">Simpan sumber asli, pilih bukti yang relevan, lalu minta analisis.</p></div><RouterLink class="button" to="/reports">← Daftar laporan</RouterLink></div>
  <ErrorNotice :error="error" /><div v-if="message" class="notice success" role="status">{{ message }}</div>
  <div v-if="unknown" class="notice warning">Hasil tindakan terakhir belum pasti. Muat kembali draft dan periksa bukti tersimpan sebelum mengulang.<button class="small" @click="load">Baca draft tersimpan</button></div>
  <div v-if="isNew" class="card start-draft"><div class="eyebrow">LANGKAH PERTAMA</div><h2>Mulai dengan draft online</h2><p>Kamu dapat menggunakan teks saja, rekaman suara, gambar, atau kombinasinya. Cakupan kejadian: banjir, gempa bumi, kebakaran, dan kecelakaan.</p><button class="primary" :disabled="locked" @click="create">Buat draft kosong</button><p class="fine">Gunakan bukti milikmu. Hindari identitas korban, nomor kontak, atau alamat privat yang tidak diperlukan.</p></div>
  <div v-else-if="loading && !detail" class="card empty" role="status">Membaca draft…</div>
  <template v-if="detail && !isNew">
    <div class="report-meta"><span>#{{ report.id.slice(0,8) }}</span><span class="badge" :class="report.preparation_status.toLowerCase()">{{ label(report.preparation_status) }}</span><span>{{ label(report.workflow_status) }}</span><button class="small" :disabled="busy||analysing||loading" @click="load">Muat ulang draft</button></div>
    <div class="steps" aria-label="Tahap laporan"><span class="current"><b>1</b> Simpan bukti</span><span :class="{current:active}"><b>2</b> Pilih & bentuk bundle</span><span><b>3</b> Analisis</span></div>
    <div v-if="!editable" class="notice">Laporan sudah dikirim dan sumbernya terkunci. Bukti serta hasil tetap dapat dibaca sesuai hak akses.</div>
    <div class="draft-grid">
      <section v-if="editable" class="card input-panel"><div class="section-heading"><div><h2>Informasi kejadian</h2><p class="muted">Pilih kanal sesuai kondisi dan bukti yang tersedia.</p></div><span class="badge">Privat</span></div>
        <form method="post" action="#" @submit.prevent="saveText"><fieldset :disabled="locked"><legend>01 · Keterangan teks</legend><label for="incident-text">Ceritakan kejadian yang kamu ketahui</label><textarea id="incident-text" v-model="text" name="text_content" rows="5" aria-describedby="text-help" placeholder="Contoh: air menggenangi jalan di…" required></textarea><div id="text-help" class="field-help"><span>Jangan menambahkan informasi yang belum diketahui.</span><span>{{ textLength(text) }}/5.000</span></div><button class="secondary" type="submit">Simpan bukti teks</button></fieldset></form>
        <form method="post" action="#" @submit.prevent="saveAudio"><fieldset :disabled="locked"><legend>02 · Rekaman suara</legend><label for="audio-file">Unggah satu audio</label><input id="audio-file" name="audio" type="file" accept=".wav,.mp3,.m4a,.mp4,.webm,audio/wav,audio/mpeg,audio/mp4,audio/webm" @change="audio=$event.target.files[0]||null"><small>WAV PCM, MP3, WebM/Opus, atau M4A/MP4-AAC tanpa video dan cover gambar · maksimal 10 MiB dan dua menit.</small><AudioRecorder :disabled="locked" @recorded="audio=$event"/><p v-if="audio" class="file-name">{{ audio.name }} · {{ size(audio.size) }}</p><audio v-if="audioUrl" :src="audioUrl" controls preload="metadata" aria-label="Dengarkan rekaman sebelum disimpan"></audio><button class="secondary" type="submit">Simpan bukti audio</button></fieldset></form>
        <form method="post" action="#" @submit.prevent="saveImages"><fieldset :disabled="locked"><legend>03 · Gambar kejadian</legend><label for="image-files">Unggah PNG atau JPEG</label><input id="image-files" name="images" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" multiple @change="images=Array.from($event.target.files)"><small>Maksimal 5 MiB dan 12 megapiksel per gambar. Bundle memakai paling banyak tiga gambar.</small><ul v-if="images.length" class="pending-files"><li v-for="file in images" :key="file.name+file.size">{{ file.name }} · {{ size(file.size) }}</li></ul><button class="secondary" type="submit">Simpan bukti gambar</button></fieldset></form>
        <p class="fine">Unggah menyimpan bukti asli. Mengubah pilihan sumber membuat bundle baru dan mempertahankan bukti serta versi sebelumnya.</p>
      </section>
      <section class="card sources-panel"><div class="section-heading"><div><h2>Bukti tersimpan</h2><p class="muted">{{ evidence.length }} dari {{ count }} bukti · pilih sumber analisis</p></div><span class="badge">{{ selected.length }} dipilih</span></div>
        <div v-if="!evidence.length" class="empty"><span class="empty-icon" aria-hidden="true">◇</span><h3>Belum ada bukti</h3><p>Simpan keterangan teks, audio, atau gambar terlebih dahulu.</p></div>
        <ul v-else class="evidence-list"><li v-for="item in evidence" :key="item.id" class="evidence-item"><div class="evidence-top"><label class="check-label"><input v-model="selected" type="checkbox" :value="item.id" :disabled="locked||!editable"><strong>{{ item.type==='TEXT'?'Keterangan teks':item.original_name }}</strong></label><span class="channel-tag">{{ item.type }}</span></div><p v-if="item.type==='TEXT'" class="evidence-text">{{ item.text_content }}</p><div class="evidence-meta">{{ size(item.byte_size) }} · {{ date(item.created_at) }}</div><template v-if="item.type!=='TEXT'"><button class="link" :disabled="!online" @click="showMedia(item)">{{ preview[item.id]?'Media telah dibuka':item.type==='IMAGE'?'Buka gambar privat':'Dengarkan audio privat' }}</button><img v-if="preview[item.id]&&item.type==='IMAGE'" class="evidence-image" :src="preview[item.id]" :alt="'Bukti gambar: '+item.original_name"><audio v-if="preview[item.id]&&item.type==='AUDIO'" :src="preview[item.id]" controls preload="metadata" :aria-label="'Bukti audio: '+item.original_name"></audio></template></li></ul>
        <button v-if="next" class="full" :disabled="loading||!online" @click="more">{{ loading?'Membaca…':'Muat bukti berikutnya' }}</button>
        <template v-if="editable"><div class="bundle-summary"><strong>{{ active?'Bundle aktif · versi '+active.version_number:'Bundle belum dibentuk' }}</strong><p>Pilih maksimal satu teks, satu audio, dan tiga gambar. Total maksimal 25 MiB.</p><button class="primary full" :disabled="locked" @click="bundle">{{ selectionSaved&&active?'Simpan sebagai bundle baru':'Simpan pilihan sebagai bundle' }}</button></div><div v-if="active" class="analysis-actions"><h3>Siap dianalisis</h3><p v-if="!selectionSaved" class="text-error">Pilihan berubah. Simpan bundle sebelum analisis.</p><p v-if="external" class="fine">Rute ini memakai Gemini: teks, transkrip, atau gambar yang relevan akan diproses layanan AI eksternal. Audio asli diproses lokal; data akun dan kredensial tidak dikirim.</p><p v-else class="fine">Kanal tunggal teks atau audio diproses melalui jalur lokal tanpa Gemini.</p><label v-if="external" class="check-label consent"><input v-model="consent" type="checkbox" :disabled="locked">Saya telah membaca informasi pemrosesan eksternal.</label><button class="primary full" :disabled="locked||held||!selectionSaved" @click="analyse">{{ analysing?'Analisis sedang berjalan…':'Analisis bundle aktif' }}</button><p v-if="held" class="fine">{{ label(detail.latest_run.status) }}. Analisis baru ditahan sampai keadaan proses dipastikan.</p><button class="link" :disabled="busy||analysing||loading||!online" @click="checkRequests">Periksa status dan hasil tersimpan</button></div></template>
      </section>
    </div>
    <div v-if="analysing" class="notice" role="status">Backend sedang memproses sumber. Kamu boleh berpindah fokus selama tab dan request tetap aktif. Jika koneksi terputus, periksa hasil tersimpan sebelum mengulang.</div>
    <div v-if="requestRows.length" class="card"><h2>Request tersimpan</h2><ul class="request-list"><li v-for="item in requestRows" :key="item.key"><strong>{{ label(item.state) }}</strong> · {{ date(item.created_at) }}<small v-if="item.error_code">{{ item.error_code }}</small></li></ul></div>
    <AnalysisResult :detail="detail" />
  </template>
</template>
