<script setup>
import { label, date } from '../domain';
import { incidentIcon } from '../report-list';
import { publicFields, publicValue } from '../publication';
import AppIcon from './AppIcon.vue';
defineProps({record:{type:Object,required:true}, preview:Boolean});
</script>
<template>
  <article class="public-incident" :data-category="record.event_type">
    <header class="incident-public-heading"><span class="incident-category-icon"><AppIcon :name="incidentIcon(record.event_type)" :size="36" /></span><div><p>INCIDENT CARD PUBLIK</p><h3>{{ label(record.event_type) }}</h3><span>#{{ record.id.slice(0,8) }} · {{ record.published_at?date(record.published_at):'Belum diterbitkan' }}</span></div></header>
    <div class="incident-public-body"><p class="public-information-tag"><AppIcon name="shield" :size="15" />{{ preview?'Pratinjau informasi publik':'Informasi publik' }}</p><dl class="public-field-grid"><div v-for="[key,title,icon] in publicFields" :key="key" class="public-field"><dt><AppIcon :name="icon" :size="17" />{{ title }}</dt><dd>{{ publicValue(record,key) }}</dd></div></dl><p class="public-incident-note"><AppIcon name="lock" :size="15" />Ringkasan publik tidak memuat bukti asli atau data akun Reporter.</p></div>
  </article>
</template>
