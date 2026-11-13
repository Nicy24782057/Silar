<script setup>
import AppIcon from './AppIcon.vue';
defineProps({compact:Boolean,brief:Boolean});
</script>
<template>
  <aside class="auth-local-help" :class="{'is-compact':compact}" aria-label="Bantuan email uji lokal">
    <AppIcon name="folder" :size="16" />
    <div v-if="compact">Berkas email uji lokal: <code>code/backend/private_outbox/</code></div>
    <div v-else><strong>BANTUAN PENGUJIAN LOKAL</strong><code>code/backend/private_outbox/</code><p>Jika memakai email berkas <code>.eml</code>, buka pesan terbaru untuk email Anda dan salin kodenya. Pengiriman melalui SMTP masuk ke kotak email penerima.</p></div>
  </aside>
</template>
