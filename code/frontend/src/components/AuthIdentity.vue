<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue';
import { theme } from '../theme';
import sourceUrl from '../assets/reference/auth-identity.svg';
import darkUrl from '../assets/reference/auth-identity-dark.svg';
const panel = ref(null), height = ref(900), source = ref('');
let observer;
const request = new AbortController();
// The artwork, masks and palette come directly from the approved SVG. Only
// vertical spacing changes when the two-panel layout becomes taller/narrower.
const artwork = computed(() => {
  if (!source.value) return theme.mode === 'dark' ? darkUrl : sourceUrl;
  const document = new DOMParser().parseFromString(source.value, 'image/svg+xml');
  const root = document.documentElement, h = Math.max(720,height.value);
  root.setAttribute('viewBox', `0 0 680 ${h}`);
  root.setAttribute('height', h);
  root.setAttribute('class', theme.mode === 'dark' ? 'theme-dark' : '');
  root.querySelector('.identity-background').setAttribute('height', h);
  root.querySelector('path.divider').setAttribute('d', `M680 0V${h}`);
  const clip = root.querySelector('#identity-clip rect');
  if (clip) clip.setAttribute('height', h);
  root.querySelector('#identity-privacy').setAttribute('transform', `translate(40 ${10+h-900})`);
  // Source bounds: copy ends at y=406; privacy starts at h-155.
  // Reserve both gaps before sizing the illustration, including short screens.
  const scale=Math.min(.52,(h-155-24-430)/377.36725);
  const x=348.55558-(96.62002+985.82068/2)*scale;
  const y=Math.max(430-3.13274*scale,Math.min(467+(h-900)*.5,h-155-24-(3.13274+377.36725)*scale));
  root.querySelector('#auth-reporting-illustration').setAttribute('transform', `translate(${x} ${y}) scale(${scale})`);
  const atmosphere = root.querySelector('#identity-atmosphere');
  atmosphere.setAttribute('transform', `translate(0 ${h-900})`);
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(root));
});
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    if (entry.contentRect.width > 0) height.value = entry.contentRect.height / entry.contentRect.width * 680;
  });
  observer.observe(panel.value);
  fetch(sourceUrl,{credentials:'omit',signal:request.signal}).then(response=>response.ok?response.text():null)
    .then(value=>{if(value)source.value=value;}).catch(()=>{ /* The original static SVG remains the fallback. */ });
});
onBeforeUnmount(() => { observer?.disconnect(); request.abort(); });
</script>
<template><section ref="panel" class="auth-identity" aria-label="SILAR — Merangkai Informasi, Memahami Situasi."><img :src="artwork" alt="Sistem Inteligensi Laporan Adaptif dan Responsif. Teks, audio, dan foto diolah menjadi narasi kejadian. SENA mengenali kategori, NARA mengurai informasi. Anda memeriksa hasil sebelum laporan dikirim. Bukti tetap privat."></section></template>
