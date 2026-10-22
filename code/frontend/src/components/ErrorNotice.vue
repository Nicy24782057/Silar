<script setup>
import { ref, watch, nextTick } from 'vue';
const props = defineProps({error:Object});
const box = ref(null);
watch(() => props.error, async value => { if (value) { await nextTick(); box.value?.focus(); } });
</script>
<template>
  <div v-if="error" ref="box" class="notice error" role="alert" tabindex="-1">
    <strong>{{ error.message }}</strong>
    <ul v-if="Object.keys(error.fields || {}).length"><li v-for="(messages, field) in error.fields" :key="field">{{ field }}: {{ messages.join(' ') }}</li></ul>
    <p v-if="error.retryAfter">Tunggu {{ error.retryAfter }} detik sebelum mencoba kembali.</p>
    <small v-if="error.requestId">ID bantuan: {{ error.requestId }}</small>
  </div>
</template>
