<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { theme, toggleTheme } from '../theme';
import AppIcon from './AppIcon.vue';
defineProps({active:{type:String,default:'beranda'}});
const route=useRoute();
const portal=computed(()=>route.path==='/public');
const sections=[['beranda','Beranda'],['alur-pelaporan','Alur pelaporan'],['sena-nara','SENA & NARA']];
</script>
<template>
  <header class="landing-nav landing-container">
    <RouterLink to="/" class="landing-brand" aria-label="SILAR, halaman utama"><img src="/brand/silar-reference.svg" alt="">SILAR</RouterLink>
    <nav aria-label="Navigasi situs SILAR">
      <template v-for="[id,title] in sections" :key="id">
        <RouterLink v-if="portal" :to="{path:'/',hash:'#'+id}">{{ title }}</RouterLink>
        <a v-else :href="'#'+id" :aria-current="active===id?'location':undefined">{{ title }}</a>
      </template>
      <RouterLink to="/public" :aria-current="portal?'page':undefined">Portal Publik</RouterLink>
    </nav>
    <div class="landing-account">
      <button class="quiet landing-theme" :aria-label="theme.mode==='dark'?'Gunakan mode terang':'Gunakan mode gelap'" :aria-pressed="theme.mode==='dark'" @click="toggleTheme"><AppIcon :name="theme.mode==='dark'?'sun':'moon'" :size="18" /></button>
      <RouterLink class="button" to="/login">Masuk</RouterLink>
      <RouterLink class="button primary" to="/register">Buat akun</RouterLink>
    </div>
  </header>
</template>
