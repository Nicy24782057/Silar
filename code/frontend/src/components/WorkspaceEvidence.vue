<script setup>
import {onBeforeUnmount,ref,watch} from 'vue';
import {api} from '../api';
import {online} from '../network';
import {size,date} from '../domain';
import AppIcon from './AppIcon.vue';
import AppDialog from './AppDialog.vue';
import FetchState from './FetchState.vue';
const props=defineProps({bundle:Object,allowed:Boolean});
const error=ref(null),loading=ref(false),selected=ref(null),url=ref(null);let sequence=0,controller;
function clear(){++sequence;controller?.abort();if(url.value)URL.revokeObjectURL(url.value);url.value=null;selected.value=null;loading.value=false;error.value=null;}
async function read(){const item=selected.value;if(!item)return;const version=++sequence;controller?.abort();controller=new AbortController();loading.value=true;error.value=null;
 try{const blob=await api(`evidence/${item.id}/media/`,{raw:true,signal:controller.signal});if(version===sequence&&props.allowed)url.value=URL.createObjectURL(blob);}
 catch(e){if(version===sequence&&e.name!=='AbortError')error.value=e;}finally{if(version===sequence)loading.value=false;}}
function open(item){clear();selected.value=item;read();}
watch([()=>props.allowed,()=>props.bundle?.id],clear);onBeforeUnmount(clear);
</script>
<template>
 <FetchState v-if="!allowed" state="error" title="Bukti tidak dapat dibuka" description="Akses mengikuti penugasan dan izin akun saat ini." :disabled="true" />
 <FetchState v-else-if="!bundle?.items?.length" state="empty" title="Bukti versi resmi belum tersedia" description="Bukti dibaca dari versi resmi laporan yang dipilih." />
 <div v-else class="ws-evidence-grid"><article v-for="entry in bundle.items" :key="entry.evidence.id" class="card ws-evidence-card" :class="{'ws-evidence-text-card':entry.evidence.type==='TEXT'}"><header class="ws-panel-heading"><div class="title-with-icon"><span class="heading-icon"><AppIcon :name="entry.evidence.type==='TEXT'?'file':entry.evidence.type==='IMAGE'?'image':'audio'" /></span><div><h2>{{ entry.evidence.type==='TEXT'?'Keterangan teks':entry.evidence.type==='IMAGE'?'Foto kejadian':'Rekaman audio' }}</h2><p v-if="entry.evidence.type==='TEXT'">{{ size(entry.evidence.byte_size) }} · {{ date(entry.evidence.created_at) }}</p></div></div></header><div class="ws-evidence-content"><template v-if="entry.evidence.type==='TEXT'"><p class="preserve ws-source-text">{{ entry.evidence.text_content }}</p><p class="fine">Sumber asli dari versi resmi {{ bundle.version_number }}.</p></template><template v-else><strong class="ws-evidence-name">{{ entry.evidence.original_name }}</strong><p class="muted">{{ size(entry.evidence.byte_size) }} · {{ date(entry.evidence.created_at) }}</p><div class="ws-evidence-footer"><small><AppIcon name="lock" :size="14" />Bukti privat</small><button :disabled="!online" @click="open(entry.evidence)"><AppIcon name="eye" :size="16" />Pratinjau</button></div></template></div></article></div>
 <p class="fine">Bukti berasal dari versi resmi dan ditampilkan tanpa penyuntingan.</p>
 <AppDialog v-if="selected" :title="selected.original_name" eyebrow="BUKTI PRIVAT" class="ws-media-dialog" caption="Bukti privat · versi resmi" @close="clear"><FetchState v-if="loading" compact title="Memuat bukti…" description="Membaca berkas yang dipilih dari sumber privat." /><FetchState v-else-if="error" state="error" compact title="Bukti belum dapat dimuat" description="Coba lagi untuk membaca berkas yang sama." :error="error" :disabled="!online" @retry="read" /><template v-else-if="url"><img v-if="selected.type==='IMAGE'" class="ws-media-image" :src="url" :alt="selected.original_name"><audio v-else :src="url" controls preload="metadata"/></template><template #actions><button @click="clear">Tutup</button></template></AppDialog>
</template>
