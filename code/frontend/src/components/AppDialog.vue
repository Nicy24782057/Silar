<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, useId } from 'vue';
import AppIcon from './AppIcon.vue';
defineProps({ title: String, caption: String });
const emit = defineEmits(['close']);
const dialog = ref(null), closeButton = ref(null), titleId = useId();
let opener = null, previousOverflow = '';
onMounted(async () => {
  opener = document.activeElement;
  previousOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  dialog.value.showModal();
  await nextTick(); closeButton.value?.focus();
});
onBeforeUnmount(() => {
  dialog.value?.close();
  document.body.style.overflow = previousOverflow;
  if (opener?.isConnected && !opener.disabled) opener.focus();
});
</script>
<template>
  <dialog ref="dialog" class="silar-dialog" :aria-labelledby="titleId" @cancel.prevent="emit('close')">
    <header class="dialog-heading">
      <div><p v-if="caption" class="dialog-caption">{{ caption }}</p><h2 :id="titleId">{{ title }}</h2></div>
      <button ref="closeButton" class="dialog-close quiet" aria-label="Tutup" @click="emit('close')"><AppIcon name="close" /></button>
    </header>
    <div class="dialog-content"><slot /></div>
    <footer v-if="$slots.actions" class="dialog-actions"><slot name="actions" /></footer>
  </dialog>
</template>
