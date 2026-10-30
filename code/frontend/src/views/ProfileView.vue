<script setup>
import { computed, ref } from 'vue';
import { api } from '../api';import { session } from '../session';import AppIcon from '../components/AppIcon.vue';import ErrorNotice from '../components/ErrorNotice.vue';
import { online } from '../network';
import { roleLabel } from '../workspace';
const initials=computed(()=>(session.user.full_name||'').trim().split(/\s+/).slice(0,2).map(p=>p[0]).join('').toUpperCase());
const name=ref(session.user.full_name);const error=ref(null);const message=ref('');const busy=ref(false);
const changed=computed(()=>name.value.trim()!==session.user.full_name);
function cancel(){name.value=session.user.full_name;error.value=null;message.value='';}
async function save(){if(busy.value||!changed.value||!online.value)return;busy.value=true;error.value=null;message.value='';try{session.user=(await api('me/',{method:'PATCH',body:{full_name:name.value.trim()}})).data;name.value=session.user.full_name;message.value='Nama profil sudah disimpan.';}catch(e){error.value=e;}finally{busy.value=false;}}
</script>
<template>
 <div class="page-heading"><div><div class="eyebrow">AKUN</div><h1>Profil Saya</h1><p class="subtitle">Periksa informasi akun dan perbarui nama lengkap Anda.</p></div><span class="page-private"><AppIcon name="shield" :size="15" />Sesuai kewenangan</span></div>
 <section class="profile-banner brand-banner"><span class="avatar">{{ initials }}</span><div><h2>{{ session.user.full_name }}</h2><span class="profile-role">{{ roleLabel(session.user.role) }}</span></div><p><AppIcon :name="session.user.email_verified_at?'check':'clock'" :size="17" />{{ session.user.email_verified_at?'Email terverifikasi':'Email belum terverifikasi' }}</p></section>
 <ErrorNotice :error="error"/><p v-if="message" class="notice success" role="status">{{ message }}</p>
 <div class="profile-grid"><section class="card profile-personal"><h2>Informasi pribadi</h2><p class="muted">Nama ini digunakan untuk mengenali akun Anda di SILAR.</p><form method="post" action="#" @submit.prevent="save"><div class="field"><label for="profile-name">Nama lengkap</label><input id="profile-name" v-model="name" name="full_name" autocomplete="name" maxlength="150" :disabled="busy" required></div><p class="fine">Ubah nama untuk mengaktifkan penyimpanan.</p><div class="actions"><button class="primary" type="submit" :disabled="busy||!online||!changed||!name.trim()"><AppIcon name="check" :size="16" />{{ busy?'Menyimpan…':'Simpan nama' }}</button><button type="button" :disabled="busy||!changed" @click="cancel">Batalkan</button></div></form><p class="fine">Hanya nama lengkap yang dapat diperbarui melalui halaman ini.</p></section><section class="card profile-account"><h2>Informasi akun</h2><dl><div><dt>Email</dt><dd>{{ session.user.email }}</dd></div><div><dt>Peran</dt><dd>{{ roleLabel(session.user.role) }}</dd></div><div><dt>Verifikasi email</dt><dd :class="{'text-success':session.user.email_verified_at}">{{ session.user.email_verified_at?'Sudah terverifikasi':'Belum terverifikasi' }}</dd></div></dl></section></div>
 <aside class="shared-info-banner"><AppIcon name="lock" :size="22" /><div><strong>Email dan peran mengikuti pengaturan akun</strong><p>Kewenangan akun tidak berubah saat Anda menyimpan nama. Informasi akun ini dibaca dari akun yang sedang masuk.</p></div></aside>
</template>
