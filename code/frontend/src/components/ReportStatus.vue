<script setup>
import AppIcon from './AppIcon.vue';
defineProps({ status: { type: Object, required: true }, compact: Boolean });
</script>
<template>
  <span class="report-status-pill" :class="{compact}" :data-tone="status.tone">
    <AppIcon :name="status.icon" :size="compact ? 13 : 14" />
    <span>{{ status.label }}</span>
  </span>
</template>
