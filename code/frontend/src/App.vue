<script setup>
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { session, signOut } from './session';
import { theme, toggleTheme } from './theme';
import { online } from './network';
import AppIcon from './components/AppIcon.vue';
import PageOutlet from './components/PageOutlet.vue';
import { isStaff, roleLabel, workspaceNavigation, ADMIN_REPORTS_PATH } from './workspace';
import { notificationState, refreshUnread } from './notifications';
const route = useRoute(), router = useRouter();
const isAuth = computed(() => Boolean(route.meta.mode));
const work = computed(() => isStaff(session.user));
const workMenu = computed(() => workspaceNavigation(session.user));
const workActivePath = computed(() => route.path.startsWith('/workspace/reports/')
  ? workMenu.value.find(item=>item.to===ADMIN_REPORTS_PATH)?.to||workMenu.value.find(item=>item.to==='/workspace/assigned')?.to||'/workspace'
  : route.path);
const workTitle = computed(() => route.meta.title || (route.path==='/profile'?'Profil':route.path==='/notifications'?'Notifikasi':route.path==='/pwa'?'Aplikasi & Koneksi':'Ruang kerja'));
const accountInitials = computed(() => (session.user?.full_name || '').trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase());
const menu = ref(false), smallScreen = ref(matchMedia('(max-width:760px)').matches);
const main = ref(null), sidebar = ref(null), menuButton = ref(null), closeButton = ref(null);
const isReporting = computed(() => route.path.startsWith('/reports/')&&!route.meta.reportSent);
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
watch(() => route.fullPath, async () => { await closeMenu(false); await nextTick(); main.value?.focus({preventScroll:true}); });
watch(() => session.user, value => { if (!value && route.meta.private) router.replace('/login'); });
watch([()=>session.user?.id,()=>route.fullPath],()=>{if(!route.meta.publicLayout&&!isAuth.value)refreshUnread();},{immediate:true});
async function exit() { await closeMenu(false); await signOut(); router.push('/login'); }
</script>
<template>
  <a class="skip" href="#main">Langsung ke isi</a>
  <Transition name="layout-change" mode="out-in" @before-leave="element=>element.setAttribute('inert','')" @leave-cancelled="element=>element.removeAttribute('inert')" @after-enter="main?.focus({preventScroll:true})">
  <main v-if="isAuth" key="auth" id="main" ref="main" class="auth-main" tabindex="-1"><PageOutlet /></main>
  <main v-else-if="route.meta.publicLayout" key="public" id="main" ref="main" class="public-main" tabindex="-1"><PageOutlet /></main>
  <div v-else key="private" class="app-frame" :class="{'workspace-frame':work}">
    <button v-if="menu" class="mobile-overlay" aria-label="Tutup navigasi" @click="closeMenu()"></button>
    <aside id="app-navigation" ref="sidebar" class="sidebar" :class="{open:menu}" :inert="smallScreen&&!menu" aria-label="Navigasi utama">
      <div class="sidebar-brand-row">
        <RouterLink class="brand" to="/" aria-label="SILAR, halaman utama">
          <span class="brand-symbol"><img class="brand-image" src="/brand/silar-reference.svg" alt=""></span>
          <span class="brand-copy"><span class="brand-wordmark">SILAR</span><small>Sistem Inteligensi Laporan<br>Adaptif dan Responsif</small></span>
        </RouterLink>
        <button ref="closeButton" class="sidebar-close quiet" aria-label="Tutup menu" @click="closeMenu()"><AppIcon name="close" /></button>
      </div>
      <div v-if="work" class="nav-group workspace-nav"><div class="nav-caption">RUANG {{ roleLabel(session.user.role).toUpperCase() }}</div><nav aria-label="Ruang kerja petugas"><RouterLink v-for="item in workMenu" :key="item.to" :to="item.to" :class="{'nav-current':workActivePath===item.to}" :aria-current="workActivePath===item.to?'page':undefined"><AppIcon :name="item.icon" />{{ item.label }}<span v-if="item.to==='/notifications'&&notificationState.unread" class="nav-count">{{ notificationState.unread }}</span></RouterLink></nav></div>
      <div v-else class="nav-group"><div class="nav-caption">PELAPORAN</div>
        <nav aria-label="Pelaporan">
          <template v-if="session.user?.role==='REPORTER'">
            <RouterLink class="nav-create" to="/reports/new" :class="{'nav-current':isReporting}" :aria-current="isReporting?'page':undefined"><AppIcon name="plus" /> Buat Laporan</RouterLink>
            <RouterLink to="/reports" :aria-current="route.path==='/reports'||route.meta.reportSent?'page':undefined"><AppIcon name="reports" /> Laporan Saya</RouterLink>
          </template>
          <RouterLink v-else-if="session.user" to="/workspace"><AppIcon name="reports" /> Ruang Akun</RouterLink>
          <template v-else><RouterLink to="/login"><AppIcon name="user" /> Masuk</RouterLink><RouterLink to="/register"><AppIcon name="plus" /> Daftar Reporter</RouterLink></template>
          <RouterLink v-if="session.user" to="/notifications"><AppIcon name="bell" /> Notifikasi<span v-if="notificationState.unread" class="nav-count">{{ notificationState.unread }}</span></RouterLink>
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
        <div v-if="session.user" class="account-chip"><span class="avatar">{{ accountInitials }}</span><span>{{ session.user.full_name }}<small>{{ roleLabel(session.user.role) }}</small></span></div>
        <button v-if="session.user" class="sidebar-logout quiet" @click="exit"><AppIcon name="logout" /> Keluar</button>
      </div>
    </aside>
    <div class="page-shell" :inert="smallScreen&&menu">
      <header class="topline">
        <div v-if="work" class="ws-breadcrumb"><RouterLink to="/workspace">Ruang kerja</RouterLink><span>/</span><strong>{{ workTitle }}</strong></div><div v-if="work" class="ws-header-account"><RouterLink to="/notifications" aria-label="Buka notifikasi"><AppIcon name="bell" :size="18" /></RouterLink><span class="avatar" :title="session.user.full_name">{{ accountInitials }}</span></div>
        <button ref="menuButton" class="mobile-menu" :aria-expanded="menu" aria-controls="app-navigation" aria-label="Buka navigasi" @click="openMenu">Menu <AppIcon name="menu" :size="18" /></button>
        <RouterLink class="mobile-brand" to="/" aria-label="SILAR, halaman utama"><img src="/brand/silar-reference.svg" alt=""><span>SILAR</span></RouterLink>
      </header>
      <div v-if="!online" class="offline-banner" role="status"><AppIcon name="alert" :size="18" /><span>Perangkat offline. Sambungkan kembali jaringan untuk membaca atau menyimpan laporan. Data privat tidak disimpan untuk penggunaan offline.</span></div>
      <main id="main" ref="main" class="content" tabindex="-1"><PageOutlet /></main>
      <footer class="app-footer"><span class="footer-private"><AppIcon name="lock" :size="13" />{{ work?'Informasi tersedia sesuai penugasan dan izin akun.':'Ruang pelaporan privat · pengiriman belum berarti publikasi.' }}</span><RouterLink to="/">SILAR</RouterLink></footer>
    </div>
  </div>
  </Transition>
</template>
