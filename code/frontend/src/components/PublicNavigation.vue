<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { theme, toggleTheme } from '../theme';
import AppIcon from './AppIcon.vue';
import AccountActions from './AccountActions.vue';
defineProps({active:{type:String,default:'beranda'}});
const route=useRoute(),opened=ref(false),panel=ref(null),trigger=ref(null);
const portal=computed(()=>route.path==='/public');
const sections=[['beranda','Beranda'],['alur-pelaporan','Alur pelaporan'],['sena-nara','SENA & NARA']];
let viewport;
async function toggleMenu(){opened.value=!opened.value;if(opened.value){await nextTick();panel.value?.querySelector('a')?.focus();}}
function closeMenu(focus=false){opened.value=false;if(focus)trigger.value?.focus();}
function keydown(event){
 if(!opened.value)return;
 if(event.key==='Escape'){event.preventDefault();closeMenu(true);}

}
function resize(event){if(!event.matches)closeMenu();}
function outside(event){if(opened.value&&!panel.value?.contains(event.target)&&!trigger.value?.contains(event.target))closeMenu();}
watch(()=>route.fullPath,()=>closeMenu());
onMounted(()=>{viewport=matchMedia('(max-width:760px)');viewport.addEventListener('change',resize);document.addEventListener('keydown',keydown);document.addEventListener('pointerdown',outside);document.addEventListener('focusin',outside);});
onBeforeUnmount(()=>{viewport?.removeEventListener('change',resize);document.removeEventListener('keydown',keydown);document.removeEventListener('pointerdown',outside);document.removeEventListener('focusin',outside);});
</script>
<template>
 <header class="landing-nav landing-container">
  <RouterLink to="/" class="landing-brand" aria-label="SILAR, halaman utama"><img src="/brand/silar-reference.svg" alt="">SILAR</RouterLink>
  <nav class="landing-desktop-nav" aria-label="Navigasi situs SILAR">
   <template v-for="[id,title] in sections" :key="id"><RouterLink v-if="portal" :to="{path:'/',hash:'#'+id}">{{ title }}</RouterLink><a v-else :href="'#'+id" :aria-current="active===id?'location':undefined">{{ title }}</a></template>
   <RouterLink to="/public" :aria-current="portal?'page':undefined">Portal Publik</RouterLink>
  </nav>
  <div class="landing-account">
   <button class="quiet landing-theme" :aria-label="theme.mode==='dark'?'Gunakan mode terang':'Gunakan mode gelap'" :aria-pressed="theme.mode==='dark'" @click="toggleTheme"><AppIcon :name="theme.mode==='dark'?'sun':'moon'" :size="18" /></button>
   <span class="landing-desktop-account"><AccountActions /></span>
   <button ref="trigger" class="landing-menu-trigger quiet" aria-controls="landing-mobile-menu" :aria-expanded="opened" :aria-label="opened?'Tutup menu situs':'Buka menu situs'" @click="toggleMenu"><AppIcon :name="opened?'close':'menu'" :size="22" /></button>
  </div>
  <Transition name="public-menu"><section v-if="opened" id="landing-mobile-menu" ref="panel" class="landing-mobile-menu" aria-label="Menu situs SILAR">
   <p class="landing-menu-caption">NAVIGASI</p>
   <nav aria-label="Navigasi situs HP"><template v-for="[id,title] in sections" :key="id"><RouterLink v-if="portal" :to="{path:'/',hash:'#'+id}" @click="closeMenu()">{{ title }}<AppIcon name="chevron" :size="17" /></RouterLink><a v-else :href="'#'+id" :aria-current="active===id?'location':undefined" @click="closeMenu()">{{ title }}<AppIcon name="chevron" :size="17" /></a></template><RouterLink to="/public" :aria-current="portal?'page':undefined" @click="closeMenu()">Portal Publik<AppIcon name="chevron" :size="17" /></RouterLink></nav>
   <div class="landing-mobile-account"><p class="landing-menu-caption">AKUN</p><div @click="event=>{if(event.target.closest('a'))closeMenu();}"><AccountActions /></div></div>
   <small>Sistem Inteligensi Laporan<br>Adaptif dan Responsif</small>
  </section></Transition>
 </header>
</template>
