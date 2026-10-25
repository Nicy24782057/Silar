<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import { api, ApiError } from '../api';
import { fieldLabels } from '../analysis';
import { date, validateText } from '../domain';
import { online } from '../network';
import { requiresStoredState, readStoredReportAction, reportRequestGuidance } from '../recovery';
import { cardForm, correctionPatch, reviewState } from '../review';
import AnalysisResult from './AnalysisResult.vue';
import EvidenceSources from './EvidenceSources.vue';
import ErrorNotice from './ErrorNotice.vue';
import AppIcon from './AppIcon.vue';
import ReportSummary from './ReportSummary.vue';
import ReportStatus from './ReportStatus.vue';
import { reportStatus } from '../report-list';
const props=defineProps({detail:{type:Object,required:true},disabled:Boolean,pendingInput:Boolean,stage:{type:String,default:'review'}});
const emit=defineEmits(['updated','working','editing','navigate']);
const report=computed(()=>props.detail.report),state=computed(()=>reviewState(props.detail));
const narrative=computed(()=>props.detail.active_narrative),card=computed(()=>props.detail.current_card);
const busy=ref(false),error=ref(null),message=ref(''),uncertainResponse=ref(false),lastKey=ref(null);
const editor=ref(null),base=ref(null),values=ref({}),original=ref({}),narrativeText=ref('');
const editorPanel=ref(null);
const reviewed=ref(false),sending=ref(false);
const reviewAcknowledged=computed({get:()=>reviewed.value||state.value.confirmed,set:value=>reviewed.value=value});
watch(busy,value=>emit('working',value));
onBeforeUnmount(()=>{emit('working',false);emit('editing',false);});
const locked=computed(()=>props.disabled||busy.value||uncertainResponse.value||!online.value);
const changedBase=computed(()=>Boolean(editor.value&&base.value?.revision!==report.value.revision));
const unsavedEditor=computed(()=>editor.value!==null);
watch(unsavedEditor,value=>emit('editing',value),{immediate:true});
const canMutate=computed(()=>!locked.value&&!props.pendingInput&&!unsavedEditor.value);
const revisionNarrative=computed(()=>narrative.value?.origin==='REPORTER_REVISION');
watch(()=>[card.value?.id,narrative.value?.id],()=>{reviewed.value=false;sending.value=false;});
async function editCard(){
  editor.value='card';error.value=null;message.value='';
  original.value=cardForm(card.value.data);values.value={...original.value};
  base.value={id:card.value.id,revision:report.value.revision};
  await nextTick();editorPanel.value?.querySelector('input,textarea')?.focus();
}
async function editNarrative(){
  editor.value='narrative';error.value=null;message.value='';narrativeText.value=narrative.value.text;
  base.value={id:narrative.value.id,revision:report.value.revision};
  await nextTick();editorPanel.value?.querySelector('textarea')?.focus();
}
function cancel(){editor.value=null;error.value=null;message.value='Koreksi dibatalkan. Versi tersimpan tetap tersedia.';}
async function readLatest(){
  const detail=(await api(`reports/${report.value.id}/`)).data;
  if(detail?.report?.id!==report.value.id)throw new ApiError('Respons laporan tidak sesuai. Muat ulang.','INVALID_RESPONSE');
  emit('updated',detail);
  return detail;
}
async function refresh(){
  busy.value=true;error.value=null;
  try{
    if(uncertainResponse.value&&lastKey.value){
      try{
        const result=await readStoredReportAction(api,report.value.id,lastKey.value);
        emit('updated',result.detail);message.value=reportRequestGuidance(result.request);
        uncertainResponse.value=['RUNNING','UNKNOWN'].includes(result.request.state);
      }catch(e){
        if(e.status!==404)throw e;
        await readLatest();
        message.value='Rekam request belum ditemukan. Keadaan laporan sudah dibaca; periksa riwayat sebelum tindakan baru.';
        uncertainResponse.value=false;
      }
    }else{await readLatest();uncertainResponse.value=false;message.value='Keadaan terbaru sudah dibaca. Isian koreksi yang terbuka tetap tersedia untuk dibandingkan.';}
  }catch(e){error.value=e;}finally{busy.value=false;}
}
async function mutate(path,body,success){
  busy.value=true;error.value=null;message.value='';sending.value=false;
  let committed=false;lastKey.value=crypto.randomUUID();
  try{
    await api(`reports/${report.value.id}/${path}/`,{method:'POST',body,key:lastKey.value});
    committed=true;await readLatest();editor.value=null;uncertainResponse.value=false;reviewed.value=false;message.value=success;
  }catch(e){
    error.value=e;
    if(committed||requiresStoredState(e)||['REVISION_CONFLICT','VERSION_CONFLICT','SOURCE_CONFLICT'].includes(e.code))uncertainResponse.value=true;
  }finally{busy.value=false;}
}
async function saveCard(){
  error.value=null;
  try{
    const patch=correctionPatch(values.value,original.value);
    if(!Object.keys(patch).length){message.value='Tidak ada perubahan informasi.';return;}
    await mutate('cards/revisions',{parent_id:base.value.id,patch,expected_revision:base.value.revision},'Versi kartu baru tersimpan. Bandingkan dan konfirmasi kembali versi aktif.');
  }catch(e){error.value=e;}
}
async function saveNarrative(){
  const problem=validateText(narrativeText.value);
  if(problem){error.value=new ApiError(problem,'INVALID_PAYLOAD');return;}
  if(narrativeText.value===narrative.value.text){message.value='Tidak ada perubahan narasi.';return;}
  await mutate('narratives/revisions',{parent_id:base.value.id,text:narrativeText.value,expected_revision:base.value.revision},'Narasi baru tersimpan. Jalankan analisis ulang secara eksplisit sebelum konfirmasi.');
}
async function analyseNarrative(){
  await mutate('analyses',{mode:'NARRATIVE_REVISION',bundle_id:report.value.active_bundle_id,narrative_id:narrative.value.id,
    input_revision:report.value.input_revision,expected_revision:report.value.revision},'Hasil analisis narasi revisi telah dibaca kembali. Periksa sebelum mengonfirmasi.');
}
async function confirm(){
  await mutate('human-verifications',{card_version_id:card.value.id,expected_revision:report.value.revision},'Versi aktif sudah dikonfirmasi. Pengiriman laporan tetap merupakan tindakan terpisah.');
}
async function submit(){
  await mutate('submit',{card_version_id:card.value.id,expected_revision:report.value.revision},'Laporan resmi berhasil dikirim dan menunggu pemeriksaan petugas.');
}
</script>
<template>
  <section aria-label="Pemeriksaan dan konfirmasi laporan">
    <ErrorNotice :error="error" /><div v-if="message" class="notice success" role="status">{{ message }}</div>
    <div v-if="uncertainResponse" class="notice warning" role="status">Keadaan tindakan perlu dibaca kembali. Isian yang terbuka belum dikirim ulang.<button :disabled="busy||!online" @click="refresh">Periksa request dan laporan tersimpan</button></div>
    <div v-if="state.submitted" class="notice">Laporan sudah dikirim pada {{ date(report.submitted_at) }}. Versi resmi terkunci. Konfirmasi Reporter, pemeriksaan Operator dan publikasi adalah tahap berbeda.</div>
    <div v-if="pendingInput&&!state.submitted" class="notice warning">Masih ada isian atau pilihan sumber yang belum disimpan. Selesaikan atau kosongkan perubahan tersebut sebelum konfirmasi dan pengiriman.</div>
    <div class="review-workspace" :class="{'stage-confirm':stage==='confirm'}"><div class="review-main">
      <section v-if="!card" v-show="stage==='review'" class="card review-result review-awaiting"><AppIcon :name="state.held?'clock':'file'" :size="35" /><h2>{{ state.held?(detail.latest_run.status==='UNKNOWN'?'Hasil belum dapat dipastikan':'Analisis sedang berjalan'):'Hasil menunggu analisis' }}</h2><p>{{ state.held?'Periksa keadaan permintaan dan hasil yang tersimpan. Analisis baru ditahan sampai proses sebelumnya dipastikan.':'Gunakan bukti aktif atau jalankan analisis ulang narasi yang sudah diperbaiki. Hasil baru akan tersedia di bagian ini.' }}</p><button v-if="state.held" :disabled="busy||!online" @click="refresh">Periksa keadaan terbaru</button></section>
      <AnalysisResult v-show="stage==='review'" :detail="detail" class="review-result"><template #actions><button v-if="card&&!state.submitted" class="small quiet edit-card-button" :disabled="locked||unsavedEditor||!state.current" @click="editCard"><AppIcon name="edit" :size="16" /> Perbaiki informasi kartu</button></template></AnalysisResult>
      <section v-show="stage==='confirm'" class="card verification-panel review-decision">
        <div class="decision-heading"><span class="heading-icon"><AppIcon :name="state.submitted?'shield':'send'" /></span><div><div class="eyebrow">{{ state.submitted?'LAPORAN RESMI':'LANGKAH BERIKUTNYA' }}</div><h2>{{ state.submitted?'Versi resmi':'Konfirmasi & kirim laporan' }}</h2></div></div>
        <p v-if="!card" class="notice">Belum ada kartu aktif untuk dikonfirmasi. Simpan bukti dan periksa hasil analisis terlebih dahulu.</p>
        <template v-else>
          <dl class="confirmation-summary"><div><dt>Versi yang diperiksa</dt><dd>v{{ state.submitted?detail.official_card?.version_number:card.version_number }}</dd></div><div><dt>Pemeriksaan Reporter</dt><dd>{{ state.confirmed||state.submitted?'Sudah dikonfirmasi':'Belum dikonfirmasi' }}</dd></div><div><dt>Pengiriman</dt><dd>{{ state.submitted?'Sudah dikirim':'Belum dikirim' }}</dd></div></dl>
          <p v-if="card.uncertain" class="notice warning">Ketidakpastian model tetap dicatat setelah konfirmasi. Bandingkan kembali informasi dengan sumber.</p>
          <p v-if="state.nonEvent&&!state.submitted" class="notice error">NON_EVENT belum dapat dikirim. Kategori tidak dapat disunting untuk melewati penahanan. Perbaiki narasi atau bukti lalu analisis ulang.</p>
          <p v-if="!state.current&&!state.submitted" class="notice warning">Kartu belum sesuai dengan sumber/hasil aktif yang lengkap. Baca keadaan tersimpan dan periksa analisis sebelum melanjutkan.</p>
          <template v-if="!state.submitted">
            <div class="decision-step"><span class="decision-number" :class="{complete:state.confirmed}"><AppIcon v-if="state.confirmed" name="check" :size="15" /><template v-else>1</template></span><div><h3>Periksa & konfirmasi</h3><p>Bandingkan kartu dengan bukti dan narasi. Koreksi informasi yang belum sesuai sebelum mengonfirmasi.</p></div></div>
            <label class="check-label consent review-consent"><input v-model="reviewAcknowledged" type="checkbox" :disabled="locked||unsavedEditor||!state.canConfirm||pendingInput||state.confirmed"><span>Saya telah membandingkan versi {{ card.version_number }} dengan bukti dan narasi.</span></label>
            <button class="full confirm-button" :class="{confirmed:state.confirmed}" :disabled="!canMutate||!state.canConfirm||!reviewed" @click="confirm"><AppIcon name="check" :size="17" />{{ state.confirmed?'Versi sudah dikonfirmasi':'Konfirmasi versi ini' }}</button>
            <div class="decision-step second"><span class="decision-number">2</span><div><h3>Kirim laporan resmi</h3><p>Laporan diteruskan kepada petugas setelah versi ini dikonfirmasi.</p></div></div>
            <p v-if="!state.canSubmit" class="field-help">{{ unsavedEditor?'Simpan atau batalkan koreksi yang masih terbuka pada tahap Periksa hasil.':pendingInput?'Selesaikan input atau perubahan bukti sebelum melanjutkan.':state.held?'Keadaan analisis perlu dipastikan sebelum pengiriman.':state.nonEvent?'Hasil NON_EVENT memerlukan perbaikan sumber dan analisis ulang.':!state.current?'Periksa hasil yang sesuai dengan sumber aktif terlebih dahulu.':'Konfirmasikan versi aktif untuk mengaktifkan pengiriman.' }}</p>
            <button class="primary full" :disabled="!canMutate||!state.canSubmit" @click="sending=true"><AppIcon name="send" :size="17" /> Kirim laporan</button>
            <div v-if="sending" class="notice submit-confirmation"><strong>Kirim versi {{ card.version_number }} sebagai laporan resmi?</strong><p>Sumber dan versi resmi akan terkunci. Pengiriman belum berarti laporan telah diperiksa atau diterbitkan oleh petugas.</p><div class="review-actions"><button class="primary" :disabled="!canMutate||!state.canSubmit" @click="submit">Kirim sekarang</button><button :disabled="busy" @click="sending=false">Batal</button></div></div>
          </template>
          <div v-else class="official-summary"><ReportStatus :status="reportStatus(report)" /><p>Versi resmi <strong>{{ detail.official_card?.version_number }}</strong> telah disimpan. Perkembangan berikutnya tersedia pada status, riwayat dan notifikasi.</p></div>
        </template>
        <button class="link" :disabled="busy||!online" @click="refresh"><AppIcon name="refresh" :size="15" /> Baca keadaan terbaru</button>
      </section>
      <section v-if="narrative" v-show="stage==='review'" class="card review-narrative"><div class="section-heading"><div class="title-with-icon"><span class="heading-icon"><AppIcon name="file" :size="18" /></span><div><h2>Narasi aktif</h2><p class="muted">Versi {{ narrative.version_number }} · {{ narrative.origin==='REPORTER_REVISION'?'Revisi Reporter':'Hasil pembentukan narasi' }}</p></div></div></div><p class="preserve narrative-copy" tabindex="0" role="region" aria-label="Isi narasi aktif">{{ narrative.text }}</p>
        <button v-if="!state.submitted" class="small" :disabled="locked||unsavedEditor" @click="editNarrative"><AppIcon name="edit" :size="16" /> Perbaiki narasi</button>
        <p class="fine">Perubahan narasi disimpan sebagai versi baru dan memerlukan analisis ulang. Bukti asli tetap dipertahankan.</p>
        <div v-if="revisionNarrative&&!state.submitted" class="analysis-actions"><h3>Analisis narasi revisi</h3><p>Analisis ulang menggunakan SENA, NARA dan Fusion pada narasi ini. Transkripsi dan pemrosesan Gemini tidak diulang.</p><button class="primary" :disabled="!canMutate||state.held" @click="analyseNarrative">{{ busy?'Memproses…':'Analisis ulang narasi ini' }}</button><p v-if="state.held" class="fine">Analisis baru ditahan sampai keadaan run sebelumnya dipastikan.</p></div>
      </section>
    </div><aside class="review-aside" aria-label="Ringkasan dan bukti">
      <ReportSummary class="review-summary" :detail="detail" />
      <EvidenceSources class="review-sources" :bundle="state.submitted?detail.official_bundle:detail.active_bundle" title="Bukti untuk perbandingan" />
    </aside></div>
    <div class="section-actions review-navigation-actions">
      <button v-if="stage==='review'" @click="emit('navigate','input')"><AppIcon name="left" :size="15" />Lihat bukti</button>
      <button v-if="stage==='review'" class="primary" :disabled="!state.current||state.nonEvent||unsavedEditor||pendingInput||locked" @click="emit('navigate','confirm')">Lanjut ke konfirmasi<AppIcon name="arrow" :size="15" /></button>
      <button v-if="stage==='confirm'" @click="emit('navigate','review')"><AppIcon name="left" :size="15" />Kembali melihat hasil</button>
      <button class="link" @click="emit('navigate','history')"><AppIcon name="history" :size="15" />Versi & riwayat</button>
    </div>
    <section v-if="editor" v-show="stage==='review'" ref="editorPanel" class="card correction-editor"><div class="section-heading"><div><h2>{{ editor==='card'?'Koreksi informasi kartu':'Revisi narasi' }}</h2><p class="muted">Perubahan disimpan sebagai versi baru pada laporan yang sama.</p></div><button class="small" :disabled="busy" @click="cancel">Batal koreksi</button></div>
      <div v-if="changedBase" class="notice warning">Laporan telah berubah sejak form ini dibuka. Isian tetap tersedia untuk dibandingkan. Batalkan form setelah membandingkan, lalu buka koreksi terhadap versi terbaru; form lama tidak dikirim ulang otomatis.</div>
      <form v-if="editor==='card'" @submit.prevent="saveCard"><fieldset :disabled="locked||changedBase"><div class="correction-fields"><div v-for="(name,key) in fieldLabels" :key="key" class="field"><label :for="'correct-'+key">{{ name }}</label><input v-if="key==='location_text'||key==='time_text'" :id="'correct-'+key" v-model="values[key]" :maxlength="key==='location_text'?500:300"><input v-else-if="key==='occurred_at'" :id="'correct-'+key" v-model="values[key]" type="datetime-local" step="1"><textarea v-else :id="'correct-'+key" v-model="values[key]" rows="3"></textarea><small v-if="key==='occurred_at'">Isi hanya jika waktu pasti diketahui dari sumber. Zona waktu mengikuti perangkat. Biarkan kosong jika belum tersedia.</small><small v-else-if="!['location_text','time_text'].includes(key)">Satu informasi per baris. Kosongkan jika belum tersedia; kosong tidak berarti tidak ada.</small></div></div><button class="primary" type="submit">Simpan versi kartu baru</button></fieldset></form>
      <form v-else @submit.prevent="saveNarrative"><fieldset :disabled="locked||changedBase"><label for="narrative-correction">Narasi yang diperbaiki</label><textarea id="narrative-correction" v-model="narrativeText" rows="7" required></textarea><p class="fine">Penyimpanan menonaktifkan kartu aktif dan memerlukan analisis ulang eksplisit. Sampaikan informasi yang diketahui dari sumber.</p><button class="primary" type="submit">Simpan versi narasi baru</button></fieldset></form>
    </section>
  </section>
</template>
