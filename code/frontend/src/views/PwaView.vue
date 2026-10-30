<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import { online } from '../network';
const prompt=ref(null);const message=ref('');const update=ref(null);
const guide=ref(false);
const capture=event=>{event.preventDefault();prompt.value=event;};
onMounted(async()=>{window.addEventListener('beforeinstallprompt',capture);if('serviceWorker'in navigator){const registration=await navigator.serviceWorker.getRegistration();update.value=registration?.waiting||null;}});
onUnmounted(()=>window.removeEventListener('beforeinstallprompt',capture));
async function install(){if(!prompt.value)return;await prompt.value.prompt();const result=await prompt.value.userChoice;message.value=result.outcome==='accepted'?'Permintaan pemasangan diterima.':'Pemasangan dibatalkan; kamu tetap dapat memakai browser.';prompt.value=null;}
function activate(){update.value?.postMessage('ACTIVATE_UPDATE');navigator.serviceWorker.addEventListener('controllerchange',()=>location.reload(),{once:true});}
</script>
<template>
 <div class="page-heading"><div><div class="eyebrow">AKSES APLIKASI</div><h1>Aplikasi & Koneksi</h1><p class="subtitle">Akses SILAR dari browser atau pasang sebagai aplikasi.</p></div><span class="page-private"><AppIcon name="shield" :size="15" />Sesuai kewenangan</span></div>
 <div class="shared-info-banner connection-banner" :class="{offline:!online}" role="status"><AppIcon :name="online?'globe':'alert'" :size="23" /><div><strong>{{ online?'Jaringan perangkat tersedia':'Perangkat sedang offline' }}</strong><p>Status layanan diperiksa saat Anda membuka data.</p></div><span class="badge">{{ online?'Online':'Offline' }}</span></div>
 <div class="info-grid connection-cards"><section class="card pwa-card"><header class="brand-banner"><span class="heading-icon"><AppIcon name="device" :size="25" /></span><h2>Pasang SILAR</h2><p>Akses dari browser atau pasang untuk membuka SILAR melalui ikon aplikasi di perangkat Anda.</p></header><div class="pwa-body"><ol class="pwa-steps"><li>Buka SILAR melalui browser.</li><li>Gunakan pilihan pemasangan yang tersedia.</li><li>Buka kembali melalui ikon aplikasi.</li></ol><button v-if="prompt" class="primary" @click="install">Pasang aplikasi</button><button v-else class="primary" @click="guide=true"><AppIcon name="device" :size="18" />Panduan pemasangan</button><p v-if="message" role="status">{{ message }}</p><button v-if="update" @click="activate">Gunakan pembaruan aplikasi</button></div></section><section class="card pwa-card"><header class="brand-banner"><span class="heading-icon"><AppIcon name="lock" :size="25" /></span><h2>Ketika offline</h2><p>Sebagian tampilan yang pernah dimuat dapat dibuka kembali.</p></header><div class="pwa-body"><h3>Tetap membutuhkan koneksi</h3><p>Masuk akun, laporan, draft, bukti, media privat, dan hasil analisis.</p><hr><p>Draft tidak disimpan atau disinkronkan secara offline.</p><p class="fine">Hubungkan perangkat sebelum melanjutkan tindakan.</p></div></section></div>
 <aside class="shared-info-banner"><AppIcon name="shield" :size="22" /><div><strong>Data privat tetap terlindungi</strong><p>Token dan data privat tidak dimasukkan ke cache aplikasi. Pemasangan aplikasi tidak memperluas kewenangan akun.</p></div></aside>
 <AppDialog v-if="guide" title="Panduan pemasangan" @close="guide=false"><p>Gunakan menu browser untuk memasang SILAR atau menambahkannya ke layar utama. Pilihan pemasangan mengikuti dukungan perangkat dan browser.</p><ol><li>Buka menu browser saat mengakses SILAR.</li><li>Pilih Pasang aplikasi atau Tambahkan ke layar utama jika tersedia.</li><li>Ikuti petunjuk browser, lalu buka melalui ikon SILAR.</li></ol><template #actions><button @click="guide=false">Tutup</button></template></AppDialog>
</template>
