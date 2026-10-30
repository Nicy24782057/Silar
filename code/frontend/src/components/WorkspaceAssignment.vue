<script setup>
import {onMounted,onBeforeUnmount,reactive,ref} from 'vue';
import {api} from '../api';
import {paginationPath} from '../domain';
import {online} from '../network';
import {requiresStoredState} from '../recovery';
import {assignmentTargetAvailable,shortId} from '../workspace';
import AppDialog from './AppDialog.vue';
import ErrorNotice from './ErrorNotice.vue';
import FetchState from './FetchState.vue';
const props=defineProps({report:{type:Object,required:true}});
const emit=defineEmits(['close','saved']);
const targets=ref([]),loading=ref(true),busy=ref(false),error=ref(null),readError=ref(null),unknown=ref(false);
const form=reactive({operator_id:'',reason:''});let sequence=0,controller,command;
async function load(){const version=++sequence;controller?.abort();controller=new AbortController();loading.value=true;readError.value=null;
 try{let path='workspace/assignment-targets/?page_size=100',rows=[];do{const r=await api(path,{signal:controller.signal});rows.push(...r.results);path=r.next?paginationPath(r.next):null;}while(path);if(version===sequence)targets.value=rows;}
 catch(e){if(version===sequence&&e.name!=='AbortError')readError.value=e;}finally{if(version===sequence)loading.value=false;}}
onMounted(load);onBeforeUnmount(()=>{++sequence;controller?.abort();});
async function save(){
 if(busy.value)return;busy.value=true;error.value=null;
 if(!command)command={key:crypto.randomUUID(),body:{expected_revision:props.report.revision,operator_id:form.operator_id,reason:form.reason.trim()}};
 try{const r=await api(`workspace/reports/${props.report.id}/assignment/`,{method:'POST',key:command.key,body:command.body});unknown.value=false;emit('saved',r.data.message);}
 catch(e){error.value=e;if(requiresStoredState(e))unknown.value=true;else{unknown.value=false;command=null;}}finally{busy.value=false;}
}
</script>
<template>
 <AppDialog eyebrow="PENUGASAN" :title="report.operator_id?'Alihkan penanggung jawab':'Tugaskan laporan'" :caption="'Laporan '+shortId(report.id)" @close="!busy&&!unknown&&emit('close')">
  <div class="ws-current-assignee"><small>Penanggung jawab saat ini</small><strong>{{ report.operator_name||'Belum ditugaskan' }}</strong></div>
  <FetchState v-if="loading" compact title="Memuat petugas yang memenuhi syarat…" /><FetchState v-else-if="readError" compact state="error" title="Daftar petugas belum dapat dimuat" description="Coba lagi untuk membaca pilihan penanggung jawab." :error="readError" :disabled="!online" @retry="load" />
  <FetchState v-else-if="!targets.filter(p=>assignmentTargetAvailable(p,report.operator_id)).length" compact state="empty" title="Belum ada petugas yang memenuhi syarat" description="Periksa aktivasi dan izin akun Operator. Pengalihan mengecualikan penanggung jawab saat ini." />
  <form v-else id="assignment-form" @submit.prevent="save"><fieldset :disabled="busy||unknown"><div class="field"><label for="assignment-person">{{ report.operator_id?'Petugas pengganti':'Penanggung jawab' }} *</label><select id="assignment-person" v-model="form.operator_id" required><option disabled value="">Pilih petugas aktif</option><option v-for="person in targets.filter(p=>assignmentTargetAvailable(p,report.operator_id))" :key="person.id" :value="person.id">{{ person.full_name }}</option></select><small>Nama mengikuti akun petugas aktif, terverifikasi, dan memenuhi izin penugasan.</small></div><div class="field"><label for="assignment-reason">Alasan {{ report.operator_id?'pengalihan':'penugasan' }} *</label><textarea id="assignment-reason" v-model="form.reason" required maxlength="1500" placeholder="Jelaskan alasan penugasan petugas." /></div></fieldset></form>
  <ErrorNotice :error="error" /><p v-if="unknown" class="notice warning">Hasil penugasan belum pasti. Periksa atau pulihkan hasil menggunakan kunci dan isi permintaan yang sama; jangan membuat penugasan kedua.</p>
  <p v-if="report.operator_id" class="notice warning">Petugas sebelumnya kehilangan akses privat dan tindakan setelah pengalihan. Riwayat penugasan tetap disimpan.</p>
  <template #actions><button :disabled="busy||unknown" @click="emit('close')">Batal</button><button v-if="unknown" class="primary" :disabled="busy||!online" @click="save">{{ busy?'Memeriksa…':'Periksa hasil penugasan' }}</button><button v-else class="primary" type="submit" form="assignment-form" :disabled="busy||loading||Boolean(readError)||!form.operator_id||!form.reason.trim()">{{ busy?'Menyimpan…':report.operator_id?'Alihkan laporan':'Tugaskan laporan' }}</button></template>
 </AppDialog>
</template>
