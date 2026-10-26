<script setup>
import {onBeforeUnmount,ref,watch} from 'vue';
import {api} from '../api';
import {size,date} from '../domain';
import AppIcon from './AppIcon.vue';
import AppDialog from './AppDialog.vue';
import ErrorNotice from './ErrorNotice.vue';
const props=defineProps({bundle:Object,allowed:Boolean});
const error=ref(null),loading=ref(null),preview=ref(null);let token=0;
function clear(){token+=1;if(preview.value)URL.revokeObjectURL(preview.value.url);preview.value=null;loading.value=null;}
async function open(item){clear();const version=token;loading.value=item.id;error.value=null;try{const blob=await api(`evidence/${item.id}/media/`,{raw:true});if(version!==token)return;preview.value={url:URL.createObjectURL(blob),item};}catch(e){if(version===token)error.value=e;}finally{if(version===token)loading.value=null;}}
watch(()=>props.allowed,value=>{if(!value)clear();});onBeforeUnmount(clear);
</script>
<template><ErrorNotice :error="error" /><p v-if="!allowed" class="notice warning">Akses bukti memerlukan penugasan sebagai penanggung jawab saat ini.</p><ul v-else class="ws-evidence-list"><li v-for="entry in bundle?.items||[]" :key="entry.evidence.id"><div class="ws-evidence-heading"><span class="heading-icon"><AppIcon :name="entry.evidence.type==='TEXT'?'file':entry.evidence.type==='IMAGE'?'image':'audio'" /></span><div><strong>{{ entry.evidence.type==='TEXT'?'Keterangan teks':entry.evidence.original_name }}</strong><small>{{ size(entry.evidence.byte_size) }} · {{ date(entry.evidence.created_at) }}</small></div><button v-if="entry.evidence.type!=='TEXT'" :disabled="loading!==null" @click="open(entry.evidence)">{{ loading===entry.evidence.id?'Memuat…':'Pratinjau' }}</button></div><p v-if="entry.evidence.type==='TEXT'" class="preserve ws-source-text">{{ entry.evidence.text_content }}</p></li></ul><p class="fine">Bukti adalah sumber dari versi resmi dan ditampilkan tanpa penyuntingan.</p><AppDialog v-if="preview" :title="preview.item.original_name" caption="Bukti versi resmi" @close="clear"><img v-if="preview.item.type==='IMAGE'" class="ws-media-image" :src="preview.url" :alt="preview.item.original_name"><audio v-else :src="preview.url" controls preload="metadata"/><template #actions><button @click="clear">Tutup</button></template></AppDialog></template>
