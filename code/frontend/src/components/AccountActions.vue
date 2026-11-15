<script setup>
import { computed } from 'vue';
import { session, restoreSession } from '../session';
import { accountHome } from '../account-routing';
import AppIcon from './AppIcon.vue';
defineProps({registerOnly:Boolean});
const home=computed(()=>accountHome(session.user));
</script>
<template>
 <span v-if="!session.ready" class="account-session-loading" role="status"><AppIcon name="refresh" class="is-spinning" :size="15" />Memeriksa sesi…</span>
 <RouterLink v-else-if="session.user" class="button primary account-resume" :to="home">Buka aplikasi<AppIcon name="arrow" :size="15" /></RouterLink>
 <template v-else-if="session.restoreError"><button class="button account-retry" @click="restoreSession({retry:true})">Periksa sesi lagi</button><RouterLink class="button" to="/login">Masuk</RouterLink></template>
 <template v-else><RouterLink v-if="!registerOnly" class="button" to="/login">Masuk</RouterLink><RouterLink class="button primary" to="/register">Buat akun</RouterLink></template>
</template>
