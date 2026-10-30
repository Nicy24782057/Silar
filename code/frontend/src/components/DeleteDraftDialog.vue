<script setup>
import { ref } from 'vue';
import { api, ApiError } from '../api';
import { online } from '../network';
import { requiresStoredState } from '../recovery';
import AppDialog from './AppDialog.vue';
import ErrorNotice from './ErrorNotice.vue';
const props=defineProps({report:{type:Object,required:true}});
const emit=defineEmits(['close','deleted','refresh']);
const busy=ref(false),unknown=ref(false),error=ref(null);
// Keep the same identity, revision and key until a terminal response is known.
const id=props.report.id,body={expected_revision:props.report.revision},key=crypto.randomUUID();
async function remove(){
 if(busy.value||!online.value)return;
 busy.value=true;error.value=null;
 try{const result=await api(`reports/${id}/`,{method:'DELETE',body,key});if(result?.data?.id!==id||!result.data.deleted_at)throw new ApiError('Hasil penghapusan belum dapat dipastikan. Periksa dengan permintaan yang sama.','RESPONSE_UNKNOWN');unknown.value=false;emit('deleted',id);}
 catch(e){error.value=e;unknown.value=requiresStoredState(e);}
 finally{busy.value=false;}
}
function close(){if(!busy.value&&!unknown.value){emit('close');if(error.value)emit('refresh');}}
</script>
<template>
 <AppDialog title="Hapus laporan yang belum dikirim?" :caption="'Laporan #'+id.slice(0,8)" @close="close">
  <p>Laporan ini akan dihapus dari daftar dan tidak dapat dilanjutkan. Bukti serta catatan yang sudah tersimpan tetap dipertahankan.</p>
  <p>Penghapusan hanya berlaku untuk laporan milik Anda yang belum dikirim.</p>
  <ErrorNotice :error="error" />
  <p v-if="unknown" class="notice warning" role="status">Respons terputus. Penghapusan mungkin sudah tersimpan. Periksa hasil dengan permintaan yang sama sebelum melanjutkan.</p>
  <template #actions><button :disabled="busy||unknown" @click="close">Batal</button><button class="danger" :disabled="busy||!online" @click="remove">{{ busy?'Memeriksa…':unknown?'Periksa hasil penghapusan':'Hapus laporan' }}</button></template>
 </AppDialog>
</template>
