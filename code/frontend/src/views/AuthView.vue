<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api, authPost, ApiError } from '../api';
import { session, signIn } from '../session';
import { online } from '../network';
import { theme, toggleTheme } from '../theme';
import { challengeFromQuery, showLocalEmailHelp, rememberVerificationEmail, takeVerificationEmail, accountVerificationResult } from '../auth-ui';
import AuthIdentity from '../components/AuthIdentity.vue';
import AppIcon from '../components/AppIcon.vue';
import AuthLocalHelp from '../components/AuthLocalHelp.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
import PasswordInput from '../components/PasswordInput.vue';
const route=useRoute(),router=useRouter();
const mode=computed(()=>route.meta.mode);
const completed=ref(false),heading=ref(null),activationToken=ref('');
const isVerification=computed(()=>['verify','activate'].includes(mode.value));
const needsCode=computed(()=>isVerification.value&&!activationToken.value||mode.value==='reset');
const hasPassword=computed(()=>['login','register','reset'].includes(mode.value)||Boolean(activationToken.value));
const challenge=computed(()=>challengeFromQuery(route.query.challenge_id));
const titles={login:'Masuk ke SILAR',register:'Buat akun Reporter',verify:'Verifikasi akun',activate:'Verifikasi akun',forgot:'Lupa kata sandi?',reset:'Atur kata sandi baru'};
const descriptions={login:'Gunakan email dan kata sandi akun Anda.',register:'Mulai menyampaikan laporan melalui SILAR.',verify:'Masukkan email dan kode enam digit dari pesan SILAR terbaru.',activate:'Masukkan email dan kode enam digit dari pesan SILAR terbaru.',forgot:'Kami mengirim petunjuk jika alamat email memenuhi syarat.',reset:'Masukkan kode dari email dan buat kata sandi baru.'};
const form=reactive({full_name:'',email:takeVerificationEmail(),password:'',password_confirm:'',code:''});
const error=ref(null),message=ref(''),busy=ref(false),successTitle=ref('');
const policy=reactive({password_min_length:15,otp_resend_seconds:60,otp_ttl_seconds:600,otp_max_attempts:5,otp_window_seconds:900});
const clock=ref(Date.now()),resendUntil=ref(0),retryUntil=ref(0);
const resendRemaining=computed(()=>Math.max(0,Math.ceil((resendUntil.value-clock.value)/1000)));
const retryRemaining=computed(()=>Math.max(0,Math.ceil((retryUntil.value-clock.value)/1000)));
const passwordLength=computed(()=>Array.from(form.password).length);
const canSubmit=computed(()=>!busy.value&&online.value&&!completed.value&&!retryRemaining.value&&(!needsCode.value||/^[0-9]{6}$/.test(form.code))&&(mode.value!=='reset'||Boolean(challenge.value))&&(!hasPassword.value||mode.value==='login'||passwordLength.value>=policy.password_min_length));
const localHelp=showLocalEmailHelp({flag:import.meta.env.VITE_AUTH_LOCAL_HELP,development:import.meta.env.DEV,hostname:location.hostname});
let flowVersion=0,timer;
watch([mode,()=>route.query.challenge_id],()=>{flowVersion++;error.value=null;message.value='';busy.value=false;completed.value=false;activationToken.value='';form.password='';form.password_confirm='';form.code='';retryUntil.value=0;},{immediate:true});
watch([completed,activationToken],async()=>{await nextTick();heading.value?.focus();});
onMounted(async()=>{timer=setInterval(()=>{clock.value=Date.now();},1000);try{const result=await api('auth/account-policy/',{auth:false});for(const key of Object.keys(policy)){const value=result.data?.[key];if(Number.isInteger(value)&&value>0)policy[key]=value;}}catch{/* Backend enforces its policy if this supplementary read fails. */}});
onBeforeUnmount(()=>{flowVersion++;clearInterval(timer);activationToken.value='';form.password='';form.password_confirm='';form.code='';});
function waitFrom(error,target){const seconds=Number(error.retryAfter);if(error.code==='RATE_LIMITED'&&Number.isFinite(seconds)&&seconds>0){clock.value=Date.now();target.value=clock.value+seconds*1000;}}
function restartVerification(){activationToken.value='';form.password='';form.password_confirm='';form.code='';error.value=null;message.value='Minta kode baru jika kode sebelumnya sudah digunakan.';}
async function submit(){
 if(!canSubmit.value)return;
 const version=flowVersion,action=mode.value;busy.value=true;error.value=null;message.value='';
 try{
  if(needsCode.value&&!/^[0-9]{6}$/.test(form.code))throw new ApiError('Masukkan kode enam digit dari pesan terbaru.','INVALID_PAYLOAD');
  if(hasPassword.value&&action!=='login'&&form.password!==form.password_confirm)throw new ApiError('Konfirmasi kata sandi belum sama.','INVALID_PAYLOAD');
  if(action==='login'){
   await signIn(form.email,form.password);if(version!==flowVersion)return;
   const next=String(route.query.next||'');await router.replace(next.startsWith('/')&&!next.startsWith('//')?next:session.user.role==='REPORTER'?'/reports':'/workspace');
  }else if(isVerification.value){
   if(activationToken.value){const result=await authPost('operators/activate/',{activation_token:activationToken.value,password:form.password,password_confirm:form.password_confirm});if(version!==flowVersion)return;message.value=result.data.message;successTitle.value='Akun Operator berhasil diaktifkan';activationToken.value='';completed.value=true;}
   else{const result=accountVerificationResult(await authPost('account/verify/',{email:form.email.trim(),code:form.code}));if(version!==flowVersion)return;message.value=result.message;if(result.next==='SET_PASSWORD')activationToken.value=result.activation_token;else{successTitle.value='Email berhasil diverifikasi';completed.value=true;}}
  }else{
   const requests={register:['register/',{full_name:form.full_name,email:form.email,password:form.password,password_confirm:form.password_confirm}],forgot:['otp/request/',{email:form.email,purpose:'PASSWORD_RESET'}],reset:['password/reset/',{challenge_id:challenge.value,code:form.code,password:form.password,password_confirm:form.password_confirm}]};
   const [endpoint,body]=requests[action];const result=await authPost(endpoint,body);if(version!==flowVersion)return;message.value=result.data.message;
   if(action==='register'){rememberVerificationEmail(form.email);await router.replace('/verify-email');}
   if(action==='reset'){successTitle.value='Kata sandi berhasil diperbarui';completed.value=true;}
  }
 }catch(e){if(version===flowVersion){error.value=e;waitFrom(e,retryUntil);}}
 finally{if(version===flowVersion){busy.value=false;form.password='';form.password_confirm='';form.code='';}}
}
async function resend(){
 if(busy.value||!online.value||resendRemaining.value)return;
 if(!form.email.trim()){error.value=new ApiError('Isi email akun terlebih dahulu.','INVALID_PAYLOAD');return;}
 const version=flowVersion;busy.value=true;error.value=null;message.value='';
 try{const result=await authPost('otp/request/',{email:form.email.trim(),purpose:'ACCOUNT_VERIFICATION'});if(version===flowVersion){message.value=result.data.message;form.code='';clock.value=Date.now();resendUntil.value=clock.value+policy.otp_resend_seconds*1000;}}
 catch(e){if(version===flowVersion){error.value=e;waitFrom(e,resendUntil);}}
 finally{if(version===flowVersion)busy.value=false;}
}
</script>
<template>
 <div class="auth-two-panel" :data-screen="isVerification?'verify':mode">
  <AuthIdentity />
  <section class="auth-panel" aria-labelledby="auth-title">
   <div class="auth-toolbar"><button class="auth-theme quiet" :aria-pressed="theme.mode==='dark'" :aria-label="theme.mode==='dark'?'Gunakan mode terang':'Gunakan mode gelap'" @click="toggleTheme"><AppIcon :name="theme.mode==='dark'?'sun':'moon'" :size="16" />{{ theme.mode==='dark'?'Mode terang':'Mode gelap' }}</button></div>
   <div class="auth-content">
    <header class="auth-heading"><h1 id="auth-title" ref="heading" tabindex="-1">{{ completed?successTitle:activationToken?'Buat kata sandi Operator':titles[mode] }}</h1><p v-if="!completed" class="auth-subtitle">{{ activationToken?'Kode sudah benar. Buat kata sandi untuk menyelesaikan aktivasi akun.':descriptions[mode] }}</p></header>
    <div v-if="!online" class="notice warning" role="status">Perangkat offline. Sambungkan kembali jaringan untuk melanjutkan.</div><div v-if="session.message" class="notice" role="status">{{ session.message }}</div><ErrorNotice :error="error" /><div v-if="message" class="notice" :class="{success:completed}" role="status">{{ message }}</div>
    <template v-if="completed"><RouterLink class="button primary full auth-login-success" to="/login">Lanjut ke Login<AppIcon name="arrow" :size="16" /></RouterLink></template>
    <template v-else>
     <p v-if="mode==='reset'&&!challenge" class="notice warning">Buka halaman ini melalui tautan pemulihan pada email terbaru, atau <RouterLink to="/forgot-password">minta petunjuk baru</RouterLink>.</p>
     <form class="auth-form" method="post" action="#" @submit.prevent="submit">
      <div v-if="mode==='register'" class="field"><label for="full_name">Nama lengkap</label><input id="full_name" v-model="form.full_name" name="full_name" placeholder="Nama lengkap Anda" autocomplete="name" required maxlength="150" :disabled="busy"></div>
      <div v-if="mode!=='reset'" class="field"><label for="email">Email</label><input id="email" v-model="form.email" name="email" type="email" placeholder="nama@example.com" autocomplete="username" autocapitalize="off" spellcheck="false" required maxlength="254" :disabled="busy" :readonly="Boolean(activationToken)"></div>
      <div v-if="needsCode" class="field auth-code-field"><label for="code">Kode verifikasi (6 digit)</label><input id="code" v-model="form.code" name="code" type="text" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" placeholder="— — — — — —" autocomplete="one-time-code" required aria-describedby="otp-help" :disabled="busy||!online||mode==='reset'&&!challenge"></div>
      <div v-if="hasPassword" class="field"><label for="password">{{ mode==='login'?'Kata sandi':'Kata sandi baru' }}</label><PasswordInput id="password" v-model="form.password" name="password" :placeholder="mode==='login'?'Masukkan kata sandi':'Buat kata sandi'" :autocomplete="mode==='login'?'current-password':'new-password'" required :minlength="mode==='login'?undefined:policy.password_min_length" maxlength="1024" :aria-describedby="mode!=='login'?'password-help':undefined" :disabled="busy" /><small v-if="mode!=='login'" id="password-help">Minimal {{ policy.password_min_length }} karakter. Gunakan beberapa kata yang tidak berkaitan. Hindari nama/email ditambah angka, pola berulang, atau urutan keyboard.</small><p v-if="mode!=='login'&&form.password" class="auth-password-length" :class="{'is-met':passwordLength>=policy.password_min_length}">{{ passwordLength>=policy.password_min_length?'Panjang minimum terpenuhi':`Masih perlu ${policy.password_min_length-passwordLength} karakter` }}. Kelayakan sandi diperiksa saat disimpan.</p></div>
      <div v-if="hasPassword&&mode!=='login'" class="field"><label for="password_confirm">Ulangi kata sandi baru</label><PasswordInput id="password_confirm" v-model="form.password_confirm" name="password_confirm" toggle-label="konfirmasi kata sandi" placeholder="Ketik kembali kata sandi" autocomplete="new-password" required :minlength="policy.password_min_length" maxlength="1024" :disabled="busy" /></div>
      <div v-if="mode==='login'" class="auth-forgot"><RouterLink to="/forgot-password">Lupa sandi?</RouterLink></div><button class="primary full auth-submit" type="submit" :disabled="!canSubmit">{{ busy?'Memproses…':retryRemaining?`Coba lagi dalam ${retryRemaining} detik`:mode==='login'?'Masuk':mode==='register'?'Buat akun Reporter':mode==='forgot'?'Kirim petunjuk pemulihan':mode==='reset'?'Simpan kata sandi baru':activationToken?'Aktifkan akun':'Verifikasi akun' }}<AppIcon v-if="mode==='login'" name="arrow" :size="16" /></button>
      <p v-if="needsCode" id="otp-help" class="auth-field-note">Kode berlaku {{ Math.ceil(policy.otp_ttl_seconds/60) }} menit dan hanya bisa dipakai sekali. Pemeriksaan dibatasi {{ policy.otp_max_attempts }} percobaan dalam {{ Math.ceil(policy.otp_window_seconds/60) }} menit.</p>
     </form>
     <p v-if="mode==='register'" class="auth-register-note">Sesudah mendaftar, Anda langsung menuju formulir kode.<br>Ambil kode enam digit dari pesan SILAR terbaru.</p>
     <form v-if="isVerification&&!activationToken" class="auth-resend-form" method="post" action="#" @submit.prevent="resend"><p class="auth-field-note">Belum menerima kode atau kodenya kedaluwarsa?</p><button class="full auth-resend-button" type="submit" :disabled="busy||!online||Boolean(resendRemaining)">{{ resendRemaining?`Kirim ulang dalam ${resendRemaining} detik`:'Kirim ulang kode' }}</button><p class="auth-field-note">Gunakan email yang diisi di atas dan kode dari pesan terbaru. Tautan email tidak wajib dibuka.</p></form>
     <button v-if="activationToken" class="link full" :disabled="busy" @click="restartVerification">Gunakan kode baru</button><AuthLocalHelp v-if="localHelp&&isVerification" brief />
    </template>
    <nav v-if="!completed" class="auth-navigation" aria-label="Navigasi akun"><template v-if="mode==='login'"><p>Belum punya akun? <RouterLink to="/register">Buat akun</RouterLink></p><RouterLink to="/verify-email">Verifikasi akun</RouterLink></template><RouterLink v-else to="/login">{{ mode==='register'?'Sudah punya akun? Login':'Kembali ke Login' }}</RouterLink></nav><AuthLocalHelp v-if="localHelp&&mode==='register'" compact /><p class="auth-security-note"><AppIcon name="lock" :size="13" />Jangan bagikan kata sandi atau kode kepada siapa pun.</p>
   </div><footer class="auth-footer">© {{ new Date().getFullYear() }} SILAR</footer>
  </section>
 </div>
</template>
