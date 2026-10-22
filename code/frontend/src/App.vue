<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { session, signOut } from './session';
const route = useRoute(); const router = useRouter();
const menu = ref(false); const online = ref(navigator.onLine); const main = ref(null);
const sync = () => online.value = navigator.onLine;
onMounted(() => { window.addEventListener('online', sync); window.addEventListener('offline', sync); });
onUnmounted(() => { window.removeEventListener('online', sync); window.removeEventListener('offline', sync); });
watch(() => route.fullPath, async () => { menu.value = false; await nextTick(); main.value?.focus(); });
watch(() => session.user, value => { if (!value && route.meta.private) router.replace('/login'); });
async function exit() { menu.value = false; await signOut(); router.push('/login'); }
</script>
<template>
  <a class="skip" href="#main">Langsung ke isi</a>
  <div class="app-frame">
    <button v-if="menu" class="mobile-overlay" aria-label="Tutup navigasi" @click="menu=false"></button>
    <aside class="sidebar" :class="{open:menu}" aria-label="Navigasi utama">
      <RouterLink class="brand" to="/"><span class="brand-mark" aria-hidden="true">S</span><span>SILAR<small>Pelaporan kejadian</small></span></RouterLink>
      <div class="nav-caption">RUANG PELAPORAN</div>
      <nav>
        <template v-if="session.user?.role==='REPORTER'">
          <RouterLink to="/reports"><span aria-hidden="true">▤</span> Laporan Saya</RouterLink>
          <RouterLink to="/reports/new"><span aria-hidden="true">＋</span> Buat Laporan</RouterLink>
        </template>
        <RouterLink v-else-if="session.user" to="/workspace"><span aria-hidden="true">▤</span> Ruang Akun</RouterLink>
        <template v-else><RouterLink to="/login">Masuk</RouterLink><RouterLink to="/register">Daftar Reporter</RouterLink></template>
        <RouterLink v-if="session.user" to="/profile"><span aria-hidden="true">○</span> Profil</RouterLink>
        <RouterLink to="/pwa"><span aria-hidden="true">◇</span> Aplikasi & Koneksi</RouterLink>
      </nav>
      <div class="sidebar-note"><strong>Laporan yang bertanggung jawab</strong><p>Gunakan bukti milik sendiri. Batasi data pribadi dan ceritakan informasi yang benar-benar diketahui.</p></div>
      <div v-if="session.user" class="account-chip"><span class="avatar">{{ session.user.full_name.slice(0,1).toUpperCase() }}</span><span>{{ session.user.full_name }}<small>{{ session.user.role }}</small></span></div>
    </aside>
    <div class="page-shell">
      <header class="topline">
        <button class="mobile-menu" :aria-expanded="menu" aria-label="Buka navigasi" @click="menu=!menu">☰</button>
        <span>Pelaporan masyarakat <span class="top-separator">/</span> <strong>SILAR</strong></span>
        <div class="top-actions"><span class="connection" :class="{offline:!online}"><i></i>{{ online?'Terhubung':'Offline' }}</span><button v-if="session.user" class="quiet small" @click="exit">Keluar</button></div>
      </header>
      <div v-if="!online" class="offline-banner" role="status">Anda sedang offline. Sambungkan kembali internet untuk membaca atau menyimpan laporan. Data privat tidak disimpan pada cache offline.</div>
      <main id="main" ref="main" class="content" tabindex="-1"><RouterView /></main>
      <footer>SILAR · Informasi kejadian diperiksa sebelum pengiriman resmi.</footer>
    </div>
  </div>
</template>
