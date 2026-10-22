<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { authPost, ApiError } from '../api';
import { session, signIn } from '../session';
import ErrorNotice from '../components/ErrorNotice.vue';
const route = useRoute(); const router = useRouter();
const mode = computed(() => route.meta.mode);
const titles = {login:'Selamat datang kembali', register:'Buat akun Reporter', verify:'Verifikasi email', forgot:'Pulihkan akses akun', reset:'Atur kata sandi baru', activate:'Aktivasi akun Operator'};
const descriptions = {login:'Masuk untuk melanjutkan laporan dan bukti milikmu.', register:'Selesaikan verifikasi email untuk menggunakan pelaporan privat.', verify:'Gunakan tautan dan kode enam digit dari email terbaru.', forgot:'Kami akan mengirim petunjuk jika alamat email memenuhi syarat.', reset:'Masukkan kode dari email dan kata sandi pengganti.', activate:'Pemilik akun menetapkan kata sandinya sendiri melalui kode aktivasi.'};
const form = reactive({full_name:'', email:'', password:'', password_confirm:'', code:'', challenge_id:''});
const error = ref(null); const message = ref(''); const busy = ref(false); const now = ref(navigator.onLine);
const hasEmail = computed(() => ['login','register','forgot','verify'].includes(mode.value));
const hasPassword = computed(() => ['login','register','reset','activate'].includes(mode.value));
watch(mode, () => { error.value=null; message.value=''; form.password=''; form.password_confirm=''; form.code=''; form.challenge_id=String(route.query.challenge_id || ''); }, {immediate:true});
async function submit() {
  busy.value=true; error.value=null; message.value='';
  try {
    if (hasPassword.value && mode.value!=='login' && form.password!==form.password_confirm) throw new ApiError('Konfirmasi kata sandi belum sama.', 'INVALID_PAYLOAD');
    if (mode.value==='login') {
      await signIn(form.email, form.password);
      const next=String(route.query.next || '');
      await router.replace(next.startsWith('/') && !next.startsWith('//') ? next : session.user.role==='REPORTER'?'/reports':'/workspace');
    } else {
      let endpoint; let body;
      if (mode.value==='register') { endpoint='register/'; body={full_name:form.full_name, email:form.email, password:form.password, password_confirm:form.password_confirm}; }
      if (mode.value==='forgot') { endpoint='otp/request/'; body={email:form.email, purpose:'PASSWORD_RESET'}; }
      if (mode.value==='verify') { endpoint='otp/verify/'; body={challenge_id:form.challenge_id, code:form.code}; }
      if (['reset','activate'].includes(mode.value)) { endpoint=mode.value==='reset'?'password/reset/':'operators/activate/'; body={challenge_id:form.challenge_id, code:form.code, password:form.password, password_confirm:form.password_confirm}; }
      const result=await authPost(endpoint, body); message.value=result.data.message;
    }
  } catch (e) { error.value=e; }
  finally { busy.value=false; form.password=''; form.password_confirm=''; }
}
async function resend() {
  if (!form.email) { error.value=new ApiError('Isi email akun untuk mengirim ulang petunjuk.', 'INVALID_PAYLOAD'); return; }
  busy.value=true; error.value=null;
  try { message.value=(await authPost('otp/request/', {email:form.email, purpose:'EMAIL_VERIFICATION'})).data.message; }
  catch(e){error.value=e;} finally{busy.value=false;}
}
</script>
<template>
  <div class="auth-layout">
    <section class="auth-intro"><div class="eyebrow">LAPORKAN DENGAN JELAS</div><h1>Informasi dari kamu.<br>Bukti yang tetap terjaga.</h1><p>Sampaikan kejadian melalui teks, rekaman suara, gambar, atau kombinasinya. Laporan dan bukti hanya dibaca sesuai kewenangan.</p><div class="intro-tags"><span>Banjir</span><span>Gempa bumi</span><span>Kebakaran</span><span>Kecelakaan</span></div></section>
    <section class="card auth-card"><div class="eyebrow">AKUN SILAR</div><h2>{{ titles[mode] }}</h2><p class="subtitle">{{ descriptions[mode] }}</p>
      <div v-if="session.message" class="notice" role="status">{{ session.message }}</div>
      <ErrorNotice :error="error" /><div v-if="message" class="notice success" role="status">{{ message }}<p v-if="['verify','activate','reset'].includes(mode)"><RouterLink to="/login">Lanjut masuk</RouterLink></p></div>
      <form method="post" action="#" @submit.prevent="submit">
        <div v-if="mode==='register'" class="field"><label for="full_name">Nama lengkap</label><input id="full_name" v-model="form.full_name" name="full_name" autocomplete="name" required maxlength="150"></div>
        <div v-if="hasEmail" class="field"><label for="email">Email {{ mode==='verify'?'untuk kirim ulang':'' }}</label><input id="email" v-model="form.email" name="email" type="email" autocomplete="username" autocapitalize="off" spellcheck="false" :required="mode!=='verify'" maxlength="254"></div>
        <template v-if="['verify','reset','activate'].includes(mode)">
          <div class="field"><label for="challenge">ID verifikasi dari tautan email</label><input id="challenge" v-model="form.challenge_id" name="challenge_id" required autocomplete="off" spellcheck="false" aria-describedby="challenge-help"><small id="challenge-help">Terisi otomatis ketika membuka tautan email terbaru.</small></div>
          <div class="field"><label for="code">Kode OTP enam digit</label><input id="code" v-model="form.code" name="code" type="text" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" autocomplete="one-time-code" required></div>
        </template>
        <div v-if="hasPassword" class="field"><label for="password">{{ mode==='login'?'Kata sandi':'Kata sandi baru' }}</label><input id="password" v-model="form.password" name="password" type="password" :autocomplete="mode==='login'?'current-password':'new-password'" required :minlength="mode==='login'?undefined:8" aria-describedby="password-help"><small id="password-help">{{ mode==='login'?'Kata sandi peka terhadap huruf besar dan kecil.':'Minimal delapan karakter; hindari nama, email, atau kata sandi umum.' }}</small></div>
        <div v-if="hasPassword && mode!=='login'" class="field"><label for="password_confirm">Ulangi kata sandi baru</label><input id="password_confirm" v-model="form.password_confirm" name="password_confirm" type="password" autocomplete="new-password" required></div>
        <button class="primary full" type="submit" :disabled="busy">{{ busy?'Memproses…':mode==='login'?'Masuk':mode==='register'?'Daftar & kirim verifikasi':mode==='forgot'?'Kirim petunjuk pemulihan':mode==='verify'?'Verifikasi email':mode==='reset'?'Simpan kata sandi baru':'Aktifkan akun' }}</button>
        <button v-if="mode==='verify'" type="button" class="full secondary" :disabled="busy" @click="resend">Kirim ulang petunjuk verifikasi</button>
      </form>
      <div class="auth-links"><RouterLink v-if="mode==='login'" to="/forgot-password">Lupa kata sandi?</RouterLink><RouterLink v-if="mode==='login'" to="/verify-email">Verifikasi email</RouterLink><RouterLink v-if="mode!=='login'" to="/login">Kembali masuk</RouterLink><RouterLink v-if="mode==='login'" to="/register">Buat akun Reporter</RouterLink></div>
      <p class="fine">Jangan bagikan kata sandi atau OTP. Cookie digunakan untuk sesi dan keamanan formulir. OTP akun berbeda dari pemeriksaan isi laporan.</p>
    </section>
  </div>
</template>
