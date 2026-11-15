<script setup>
import { theme, toggleTheme } from '../theme';
import AppIcon from './AppIcon.vue';
import ReferenceArt from './ReferenceArt.vue';
import scene from '../assets/reference/auth-mobile-scene.svg';
import sceneDark from '../assets/reference/auth-mobile-scene-dark.svg';
defineProps({compact:Boolean});
</script>
<template>
 <header class="mobile-auth-header" :class="{'is-compact':compact}">
  <RouterLink class="mobile-auth-control mobile-auth-back" to="/" aria-label="Kembali ke beranda"><AppIcon name="left" :size="18" /></RouterLink>
  <button class="mobile-auth-control mobile-auth-theme" :aria-label="theme.mode==='dark'?'Gunakan mode terang':'Gunakan mode gelap'" :aria-pressed="theme.mode==='dark'" @click="toggleTheme"><AppIcon :name="theme.mode==='dark'?'sun':'moon'" :size="18" /></button>
  <RouterLink class="mobile-auth-brand" to="/" aria-label="SILAR, halaman utama"><img src="/brand/silar-reference.svg" alt=""><strong>SILAR</strong></RouterLink>
  <p class="mobile-auth-tagline">Merangkai informasi. Memahami situasi.</p>
  <ReferenceArt class="mobile-auth-scene" :source="scene" :dark-source="sceneDark" alt="" />
 </header>
</template>
