<script setup>
import {onMounted,reactive,ref} from 'vue';
import {api} from '../api';
import {paginationPath} from '../domain';
import {assignmentTargetAvailable,shortId} from '../workspace';
import AppDialog from './AppDialog.vue';
import ErrorNotice from './ErrorNotice.vue';
const props=defineProps({report:{type:Object,required:true}});
const emit=defineEmits(['close','saved']);
const targets=ref([]),loading=ref(true),busy=ref(false),error=ref(null);
const form=reactive({operator_id:'',reason:''});
onMounted(async()=>{try{let path='workspace/assignment-targets/?page_size=100';do{const r=await api(path);targets.value.push(...r.results);path=r.next?paginationPath(r.next):null;}while(path);}catch(e){error.value=e;}finally{loading.value=false;}});
async function save(){
  if(busy.value)return;busy.value=true;error.value=null;
  try{const r=await api(`workspace/reports/${props.report.id}/assignment/`,{method:'POST',key:crypto.randomUUID(),
    body:{expected_revision:props.report.revision,operator_id:form.operator_id,reason:form.reason.trim()}});emit('saved',r.data.message);}
  catch(e){error.value=e;}finally{busy.value=false;}
}
</script>
<template>
  <AppDialog :title="report.operator_id?'Alihkan penanggung jawab':'Tugaskan laporan'" :caption="'Laporan '+shortId(report.id)" @close="!busy&&emit('close')">
    <ErrorNotice :error="error" />
    <div class="ws-current-assignee"><small>Penanggung jawab saat ini</small><strong>{{ report.operator_name||'Belum ditugaskan' }}</strong></div>
    <form id="assignment-form" @submit.prevent="save">
      <div class="field"><label for="assignment-person">{{ report.operator_id?'Petugas pengganti':'Penanggung jawab' }} *</label>
        <select id="assignment-person" v-model="form.operator_id" required :disabled="busy||loading"><option disabled value="">{{ loading?'Membaca petugas…':'Pilih petugas aktif' }}</option><option v-for="person in targets.filter(p=>assignmentTargetAvailable(p,report.operator_id))" :key="person.id" :value="person.id">{{ person.full_name }}</option></select>
        <small>Nama mengikuti akun petugas yang aktif, terverifikasi, dan memenuhi izin penugasan.</small>
      </div>
      <p v-if="!loading&&!targets.filter(p=>assignmentTargetAvailable(p,report.operator_id)).length" class="notice warning">Belum ada petugas pengganti yang memenuhi syarat. Periksa aktivasi dan izin akun Operator.</p>
      <div class="field"><label for="assignment-reason">Alasan {{ report.operator_id?'pengalihan':'penugasan' }} *</label><textarea id="assignment-reason" v-model="form.reason" required maxlength="1500" :disabled="busy" placeholder="Jelaskan alasan penugasan petugas." /></div>
    </form>
    <p v-if="report.operator_id" class="notice warning">Petugas sebelumnya kehilangan akses privat dan tindakan setelah pengalihan. Riwayat penugasan tetap disimpan.</p>
    <template #actions><button :disabled="busy" @click="emit('close')">Batal</button><button class="primary" type="submit" form="assignment-form" :disabled="busy||loading||!form.operator_id||!form.reason.trim()">{{ busy?'Menyimpan…':report.operator_id?'Alihkan laporan':'Tugaskan laporan' }}</button></template>
  </AppDialog>
</template>
