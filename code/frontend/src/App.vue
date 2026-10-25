<script setup>
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { session, signOut } from './session';
import { theme, toggleTheme } from './theme';
import { online } from './network';
import AppIcon from './components/AppIcon.vue';
const route = useRoute(), router = useRouter();
const isAuth = computed(() => Boolean(route.meta.mode));
const accountInitials = computed(() => (session.user?.full_name || '').trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase());
const menu = ref(false), smallScreen = ref(matchMedia('(max-width:760px)').matches);
const main = ref(null), sidebar = ref(null), menuButton = ref(null), closeButton = ref(null);
const isReporting = computed(() => route.path.startsWith('/reports/') && route.params.id !== 'new');
let viewport, previousOverflow = '';
async function closeMenu(returnFocus = true) {
  menu.value = false;
  if (returnFocus) { await nextTick(); menuButton.value?.focus(); }
}
async function openMenu() { menu.value = true; await nextTick(); closeButton.value?.focus(); }
function keyboardMenu(event) {
  if (!menu.value || !smallScreen.value) return;
  if (event.key === 'Escape') { event.preventDefault(); closeMenu(); }
  if (event.key === 'Tab') {
    const focusable = [...sidebar.value.querySelectorAll('a[href],button:not(:disabled)')].filter(item => item.getClientRects().length);
    const first = focusable[0], last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  }
}
function resize(event) { smallScreen.value = event.matches; if (!event.matches) closeMenu(false); }
watch(menu, value => {
  if (value) { previousOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden'; }
  else document.body.style.overflow = previousOverflow;
});
onMounted(() => {
  viewport = matchMedia('(max-width:760px)'); viewport.addEventListener('change', resize);
  window.addEventListener('keydown', keyboardMenu);
});
onUnmounted(() => {
  viewport?.removeEventListener('change', resize); window.removeEventListener('keydown', keyboardMenu);
  if (menu.value) document.body.style.overflow = previousOverflow;
});
watch(() => route.fullPath, async () => { await closeMenu(false); await nextTick(); main.value?.focus(); });
watch(() => session.user, value => { if (!value && route.meta.private) router.replace('/login'); });
async function exit() { await closeMenu(false); await signOut(); router.push('/login'); }
</script>
<template>
  <a class="skip" href="#main">Langsung ke isi</a>
  <main v-if="isAuth" id="main" ref="main" class="auth-main" tabindex="-1"><RouterView /></main>
  <div v-else class="app-frame">
    <button v-if="menu" class="mobile-overlay" aria-label="Tutup navigasi" @click="closeMenu()"></button>
    <aside id="app-navigation" ref="sidebar" class="sidebar" :class="{open:menu}" :inert="smallScreen&&!menu" aria-label="Navigasi utama">
      <div class="sidebar-brand-row">
        <RouterLink class="brand" to="/" aria-label="SILAR, halaman utama">
          <span class="brand-symbol"><img class="brand-image" src="/brand/silar-logo.png" alt=""></span>
          <span class="brand-copy"><span class="brand-wordmark">SILAR</span><small>Sistem Inteligensi Laporan<br>Adaptif dan Responsif</small></span>
        </RouterLink>
        <button ref="closeButton" class="sidebar-close quiet" aria-label="Tutup menu" @click="closeMenu()"><AppIcon name="close" /></button>
      </div>
      <div class="nav-group"><div class="nav-caption">PELAPORAN</div>
        <nav aria-label="Pelaporan">
          <template v-if="session.user?.role==='REPORTER'">
            <RouterLink class="nav-create" to="/reports/new"><AppIcon name="plus" /> Buat Laporan</RouterLink>
            <RouterLink to="/reports" :class="{'nav-current':isReporting}" :aria-current="isReporting?'page':undefined"><AppIcon name="reports" /> Laporan Saya</RouterLink>
          </template>
          <RouterLink v-else-if="session.user" to="/workspace"><AppIcon name="reports" /> Ruang Akun</RouterLink>
          <template v-else><RouterLink to="/login"><AppIcon name="user" /> Masuk</RouterLink><RouterLink to="/register"><AppIcon name="plus" /> Daftar Reporter</RouterLink></template>
          <RouterLink v-if="session.user" to="/notifications"><AppIcon name="bell" /> Notifikasi</RouterLink>
        </nav>
      </div>
      <div class="nav-group"><div class="nav-caption">APLIKASI</div>
        <nav aria-label="Aplikasi">
          <button class="sidebar-theme" :aria-pressed="theme.mode==='dark'" :aria-label="theme.mode==='dark'?'Gunakan mode terang':'Gunakan mode gelap'" @click="toggleTheme"><AppIcon :name="theme.mode==='dark'?'sun':'moon'" />{{ theme.mode==='dark'?'Mode Terang':'Mode Gelap' }}</button>
          <RouterLink to="/pwa"><AppIcon name="device" /> Aplikasi & Koneksi</RouterLink>
        </nav>
      </div>
      <div v-if="session.user" class="nav-group"><div class="nav-caption">AKUN</div><nav aria-label="Akun"><RouterLink to="/profile"><AppIcon name="user" /> Profil</RouterLink></nav></div>
      <div class="sidebar-bottom">
        <span class="connection" :class="{offline:!online}"><i></i><span>{{ online?'Jaringan tersedia':'Perangkat offline' }}</span></span>
        <div v-if="session.user" class="account-chip"><span class="avatar">{{ accountInitials }}</span><span>{{ session.user.full_name }}<small>{{ session.user.role==='REPORTER'?'Reporter':session.user.role }}</small></span></div>
        <button v-if="session.user" class="sidebar-logout quiet" @click="exit"><AppIcon name="logout" /> Keluar</button>
      </div>
    </aside>
    <div class="page-shell" :inert="smallScreen&&menu">
      <header class="topline">
        <button ref="menuButton" class="mobile-menu" :aria-expanded="menu" aria-controls="app-navigation" aria-label="Buka navigasi" @click="openMenu">Menu <AppIcon name="menu" :size="18" /></button>
        <RouterLink class="mobile-brand" to="/" aria-label="SILAR, halaman utama"><img src="/brand/silar-logo.png" alt=""><span>SILAR</span></RouterLink>
      </header>
      <div v-if="!online" class="offline-banner" role="status"><AppIcon name="alert" :size="18" /><span>Perangkat offline. Sambungkan kembali jaringan untuk membaca atau menyimpan laporan. Data privat tidak disimpan untuk penggunaan offline.</span></div>
      <main id="main" ref="main" class="content" tabindex="-1"><RouterView /></main>
      <footer class="app-footer"><span>Informasi kejadian diperiksa sebelum pengiriman resmi.</span><span class="footer-private"><AppIcon name="lock" :size="13" /> Ruang pelaporan privat</span></footer>
    </div>
  </div>
</template>
