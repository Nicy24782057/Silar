<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { authPost, ApiError } from '../api';
import { session, signIn } from '../session';
import { online } from '../network';
import { theme, toggleTheme } from '../theme';
import { challengeFromQuery, showLocalEmailHelp } from '../auth-ui';
import identity from '../assets/auth-identity.svg';
import AppIcon from '../components/AppIcon.vue';
import AuthLocalHelp from '../components/AuthLocalHelp.vue';
import ErrorNotice from '../components/ErrorNotice.vue';

const route = useRoute(), router = useRouter();
const mode = computed(() => route.meta.mode);
const registered = ref(false), completed = ref(false), heading = ref(null);
const screen = computed(() => mode.value === 'register' && registered.value ? 'registered' : mode.value);
const titles = {login:'Login', register:'Registrasi', registered:'Periksa Email', verify:'Verifikasi OTP', forgot:'Pulihkan akses akun', reset:'Atur kata sandi baru', activate:'Aktivasi akun Operator'};
const descriptions = {
  login:'Masuk untuk melanjutkan laporan dan bukti milikmu.', register:'Buat akun Reporter untuk mulai melapor.',
  registered:'Periksa pesan SILAR terbaru untuk melanjutkan.', verify:'Masukkan kode dari pesan yang sama dengan tautan ini.',
  forgot:'Kami akan mengirim petunjuk jika alamat email memenuhi syarat.', reset:'Masukkan kode dari email dan kata sandi pengganti.',
  activate:'Pemilik akun menetapkan kata sandinya sendiri melalui kode aktivasi.'
};
const form = reactive({full_name:'', email:'', password:'', password_confirm:'', code:''});
const error = ref(null), message = ref(''), busy = ref(false);
const challenge = computed(() => challengeFromQuery(route.query.challenge_id));
const requiresLink = computed(() => ['verify','reset','activate'].includes(mode.value));
const hasPassword = computed(() => ['login','register','reset','activate'].includes(mode.value));
const localHelp = showLocalEmailHelp({flag:import.meta.env.VITE_AUTH_LOCAL_HELP, development:import.meta.env.DEV, hostname:location.hostname});
const canSubmit = computed(() => !busy.value && online.value && !completed.value &&
  (!requiresLink.value || Boolean(challenge.value) && /^[0-9]{6}$/.test(form.code)));
let flowVersion = 0;

watch([mode, () => route.query.challenge_id], () => {
  flowVersion += 1; error.value = null; message.value = ''; busy.value = false;
  registered.value = false; completed.value = false;
  form.password = ''; form.password_confirm = ''; form.code = '';
}, {immediate:true});
watch(screen, async () => { await nextTick(); heading.value?.focus(); });

async function submit() {
  if (busy.value || completed.value) return;
  const version = flowVersion, action = mode.value;
  busy.value = true; error.value = null; message.value = '';
  try {
    if (!online.value) throw new ApiError('Sambungkan internet untuk melanjutkan.', 'OFFLINE');
    if (requiresLink.value && !challenge.value) throw new ApiError('Buka tautan dari pesan SILAR terbaru sebelum memasukkan kode.', 'INVALID_CHALLENGE');
    if (requiresLink.value && !/^[0-9]{6}$/.test(form.code)) throw new ApiError('Masukkan kode enam digit dari pesan yang sama dengan tautan.', 'INVALID_PAYLOAD');
    if (hasPassword.value && action !== 'login' && form.password !== form.password_confirm) throw new ApiError('Konfirmasi kata sandi belum sama.', 'INVALID_PAYLOAD');
    if (action === 'login') {
      await signIn(form.email, form.password);
      if (version !== flowVersion) return;
      const next = String(route.query.next || '');
      await router.replace(next.startsWith('/') && !next.startsWith('//') ? next : session.user.role === 'REPORTER' ? '/reports' : '/workspace');
    } else {
      const requests = {
        register:['register/', {full_name:form.full_name, email:form.email, password:form.password, password_confirm:form.password_confirm}],
        forgot:['otp/request/', {email:form.email, purpose:'PASSWORD_RESET'}],
        verify:['otp/verify/', {challenge_id:challenge.value, code:form.code}],
        reset:['password/reset/', {challenge_id:challenge.value, code:form.code, password:form.password, password_confirm:form.password_confirm}],
        activate:['operators/activate/', {challenge_id:challenge.value, code:form.code, password:form.password, password_confirm:form.password_confirm}]
      };
      const [endpoint, body] = requests[action];
      const result = await authPost(endpoint, body);
      if (version !== flowVersion) return;
      message.value = result.data.message;
      if (action === 'register') registered.value = true;
      if (['verify','reset','activate'].includes(action)) completed.value = true;
      await nextTick();
      if (completed.value) heading.value?.focus();
    }
  } catch (e) { if (version === flowVersion) error.value = e; }
  finally {
    if (version === flowVersion) { busy.value = false; form.password = ''; form.password_confirm = ''; form.code = ''; }
  }
}

async function resend() {
  if (busy.value) return;
  const version = flowVersion;
  error.value = null; message.value = '';
  if (!online.value) { error.value = new ApiError('Sambungkan internet untuk meminta petunjuk.', 'OFFLINE'); return; }
  if (!form.email.trim()) { error.value = new ApiError('Isi email akun untuk mengirim ulang petunjuk.', 'INVALID_PAYLOAD'); return; }
  busy.value = true;
  try {
    const result = await authPost('otp/request/', {email:form.email, purpose:'EMAIL_VERIFICATION'});
    if (version === flowVersion) { message.value = result.data.message; form.code = ''; }
  } catch (e) { if (version === flowVersion) error.value = e; }
  finally { if (version === flowVersion) busy.value = false; }
}
</script>

<template>
  <div class="auth-two-panel" :data-screen="screen">
    <section class="auth-identity" aria-label="SILAR, Sistem Inteligensi Laporan Adaptif dan Responsif"><img :src="identity" alt="" width="648" height="768"></section>
    <section class="auth-panel" aria-labelledby="auth-title">
      <div class="auth-toolbar">
        <RouterLink class="auth-mobile-brand" to="/login" aria-label="SILAR, Login"><img src="/brand/silar-logo.png" alt=""><span>SILAR</span></RouterLink>
        <button class="auth-theme quiet" :aria-pressed="theme.mode==='dark'" :aria-label="theme.mode==='dark'?'Gunakan mode terang':'Gunakan mode gelap'" @click="toggleTheme"><AppIcon :name="theme.mode==='dark'?'sun':'moon'" :size="16" />{{ theme.mode==='dark'?'Mode terang':'Mode gelap' }}</button>
      </div>
      <div class="auth-content">
        <header class="auth-heading">
          <h1 id="auth-title" ref="heading" tabindex="-1">{{ completed?'Verifikasi selesai':titles[screen] }}</h1>
          <p v-if="screen==='registered'" class="auth-generic-message" role="status">{{ message }}</p>
          <p v-if="!completed && screen!=='registered'" class="auth-subtitle">{{ descriptions[screen] }}</p>
        </header>
        <div v-if="!online" class="notice warning auth-offline" role="status">Perangkat offline. Sambungkan kembali jaringan untuk melanjutkan.</div>
        <div v-if="session.message" class="notice" role="status">{{ session.message }}</div>
        <ErrorNotice :error="error" />
        <div v-if="message && screen!=='registered'" class="notice" :class="{success:completed}" role="status">{{ message }}</div>

        <template v-if="screen==='registered'">
          <ol class="auth-email-steps">
            <li><span>1</span><div><strong>Buka pesan SILAR terbaru</strong><p>Gunakan pesan untuk email yang Anda daftarkan.</p></div></li>
            <li><span>2</span><div><strong>Buka tautan verifikasi pada pesan</strong><p>Tautan menyiapkan halaman verifikasi.</p></div></li>
            <li><span>3</span><div><strong>Masukkan kode enam digit</strong><p>Gunakan kode dari pesan yang sama dengan tautan.</p></div></li>
          </ol>
          <AuthLocalHelp v-if="localHelp" />
          <form class="auth-resend-registered" method="post" action="#" @submit.prevent="resend">
            <p>Belum menerima petunjuk?</p>
            <button class="link" type="submit" :disabled="busy||!online">{{ busy?'Memproses…':'Kirim ulang petunjuk verifikasi' }}</button>
          </form>
        </template>

        <template v-else-if="completed">
          <RouterLink class="button primary full auth-login-success" to="/login">Lanjut ke Login<AppIcon name="arrow" :size="16" /></RouterLink>
        </template>

        <template v-else>
          <template v-if="requiresLink">
            <div v-if="challenge" class="auth-link-state"><AppIcon name="check" :size="15" />Dibuka dari tautan email</div>
            <div v-else class="notice warning auth-link-missing" role="status">{{ route.query.challenge_id?'Tautan verifikasi tidak lengkap atau formatnya tidak sesuai.':'Buka halaman ini melalui tautan pada pesan SILAR terbaru.' }} <template v-if="mode==='verify'">Buka tautan terbaru atau minta ulang petunjuk melalui email di bawah.</template><template v-else-if="mode==='reset'">Buka tautan terbaru atau <RouterLink to="/forgot-password">minta petunjuk pemulihan baru</RouterLink>.</template><template v-else>Hubungi pengelola akun jika memerlukan tautan aktivasi baru.</template></div>
          </template>
          <form class="auth-form" method="post" action="#" @submit.prevent="submit">
            <div v-if="mode==='register'" class="field"><label for="full_name">Nama lengkap</label><input id="full_name" v-model="form.full_name" name="full_name" placeholder="Nama lengkap Anda" autocomplete="name" required maxlength="150" :disabled="busy"></div>
            <div v-if="['login','register','forgot'].includes(mode)" class="field"><label for="email">Email</label><input id="email" v-model="form.email" name="email" type="email" placeholder="nama@example.com" autocomplete="username" autocapitalize="off" spellcheck="false" required maxlength="254" :disabled="busy"></div>
            <div v-if="requiresLink" class="field auth-code-field"><label for="code">Kode verifikasi (6 digit)</label><input id="code" v-model="form.code" name="code" type="text" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" placeholder="— — — — — —" autocomplete="one-time-code" required aria-describedby="otp-help" :disabled="busy||!challenge||!online"></div>
            <div v-if="hasPassword" class="field">
              <label for="password">{{ mode==='login'?'Kata sandi':'Kata sandi baru' }}</label><input id="password" v-model="form.password" name="password" type="password" :placeholder="mode==='login'?'Masukkan kata sandi':'Buat kata sandi'" :autocomplete="mode==='login'?'current-password':'new-password'" required :minlength="mode==='login'?undefined:8" maxlength="1024" :aria-describedby="mode!=='login'?'password-help':undefined" :disabled="busy">
              <small v-if="mode!=='login'" id="password-help">Minimal 8 karakter; hindari nama, email, atau kata sandi umum.</small>
            </div>
            <div v-if="hasPassword && mode!=='login'" class="field"><label for="password_confirm">Ulangi kata sandi baru</label><input id="password_confirm" v-model="form.password_confirm" name="password_confirm" type="password" placeholder="Ketik kembali kata sandi" autocomplete="new-password" required minlength="8" maxlength="1024" :disabled="busy"></div>
            <div v-if="mode==='login'" class="auth-forgot"><RouterLink to="/forgot-password">Lupa sandi?</RouterLink></div>
            <button class="primary full auth-submit" type="submit" :disabled="!canSubmit">{{ busy?'Memproses…':mode==='login'?'Login':mode==='register'?'Daftar & kirim petunjuk verifikasi':mode==='forgot'?'Kirim petunjuk pemulihan':mode==='verify'?'Verifikasi email':mode==='reset'?'Simpan kata sandi baru':'Aktifkan akun' }}</button>
            <p v-if="requiresLink" id="otp-help" class="auth-field-note">Kode sekali pakai. Masa berlaku tercantum pada pesan.</p>
          </form>
          <p v-if="mode==='register'" class="auth-register-note">Setelah mendaftar, buka pesan SILAR terbaru.<br>Ikuti tautannya, lalu masukkan kode <strong>enam digit.</strong></p>
          <form v-if="mode==='verify'" class="auth-resend-form" method="post" action="#" @submit.prevent="resend">
            <div class="field"><label for="resend-email">Email untuk kirim ulang petunjuk</label><input id="resend-email" v-model="form.email" name="email" type="email" placeholder="nama@example.com" autocomplete="email" autocapitalize="off" spellcheck="false" required maxlength="254" :disabled="busy"></div>
            <button class="full auth-resend-button" type="submit" :disabled="busy||!online">{{ busy?'Memproses…':'Kirim ulang petunjuk verifikasi' }}</button>
            <p class="auth-field-note">Sesudah kirim ulang, gunakan tautan dan kode terbaru.</p>
          </form>
          <AuthLocalHelp v-if="localHelp && mode==='verify'" brief />
        </template>

        <nav v-if="!completed" class="auth-navigation" aria-label="Navigasi akun">
          <template v-if="mode==='login'"><p>Belum punya akun? <RouterLink to="/register">Buat akun</RouterLink></p><RouterLink to="/verify-email">Verifikasi email</RouterLink></template>
          <RouterLink v-else to="/login">{{ screen==='register'?'Sudah punya akun? Login':'Kembali ke Login' }}</RouterLink>
        </nav>
        <AuthLocalHelp v-if="localHelp && screen==='register'" compact />
        <p v-if="['login','registered','forgot'].includes(screen) || completed" class="auth-security-note"><AppIcon name="lock" :size="13" />Jangan bagikan kata sandi atau kode OTP kepada siapa pun.</p>
      </div>
    </section>
  </div>
</template>
