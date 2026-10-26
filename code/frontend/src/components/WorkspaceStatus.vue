<script setup>
import {workspaceLabel,statusTone} from '../workspace';
defineProps({value:String});
</script>
<template><span class="ws-badge" :class="'tone-'+statusTone(value)">{{ workspaceLabel(value) }}</span></template>
