<script setup>
import {onBeforeUnmount,ref,watch} from 'vue';
import {useRoute,useRouter} from 'vue-router';
import {api,ApiError} from '../api';
import {date} from '../domain';
import AppIcon from '../components/AppIcon.vue';
import FetchState from '../components/FetchState.vue';
const route=useRoute(),router=useRouter();
const report=ref(null),loading=ref(true),error=ref(null);let generation=0,controller;
async function load(){
 const version=++generation,id=route.params.id;controller?.abort();controller=new AbortController();loading.value=true;error.value=null;report.value=null;
 try{const detail=(await api(`reports/${id}/`,{signal:controller.signal})).data;if(version!==generation)return;
  if(detail?.report?.id!==id)throw new ApiError('Konfirmasi tidak sesuai dengan laporan.','INVALID_RESPONSE');
  if(!detail.report.submitted_at){await router.replace('/reports/'+id);return;}
  if(!detail.report.official_card_version_id||!detail.official_card)throw new ApiError('Versi resmi belum dapat dipastikan. Muat ulang untuk memeriksa.','INVALID_RESPONSE');
  report.value=detail.report;
 }catch(e){if(version===generation&&e.name!=='AbortError')error.value=e;}finally{if(version===generation)loading.value=false;}
}
watch(()=>route.params.id,load,{immediate:true});onBeforeUnmount(()=>{generation++;controller?.abort();});
</script>
<template>
 <FetchState v-if="loading" title="Memastikan pengiriman laporan…" description="Membaca waktu kirim dan versi resmi yang tersimpan." />
 <FetchState v-else-if="error" state="error" title="Konfirmasi pengiriman belum dapat dimuat" description="Muat ulang untuk memeriksa keadaan laporan. Jangan mengirim laporan kedua." :error="error" @retry="load" />
 <section v-else-if="report" class="card report-sent-page" aria-labelledby="report-sent-title">
  <div class="report-sent-symbol" aria-hidden="true"><AppIcon name="check" :size="42" /></div>
  <p class="eyebrow">PENGIRIMAN BERHASIL</p><h1 id="report-sent-title">Laporan Anda sudah terkirim</h1>
  <p class="report-sent-lead">Terima kasih telah menyampaikan laporan.<br>Pantau perkembangan laporan Anda melalui <strong>Laporan Saya</strong>.</p>
  <dl class="report-sent-receipt"><div><dt>Nomor laporan</dt><dd>#{{ report.id.slice(0,8) }}</dd></div><div><dt>Dikirim pada</dt><dd>{{ date(report.submitted_at) }}</dd></div></dl>
  <p class="report-sent-note"><AppIcon name="shield" :size="18" />Laporan telah diteruskan untuk penanganan petugas. Bukti tetap privat; pengiriman belum berarti publikasi.</p>
  <div class="report-sent-actions"><RouterLink class="button primary" to="/reports">Ke Laporan Saya<AppIcon name="arrow" :size="17" /></RouterLink><RouterLink class="button" :to="'/reports/'+report.id">Lihat rincian laporan</RouterLink></div>
 </section>
</template>
