<script setup>
import {computed,onMounted,onBeforeUnmount,reactive,ref} from 'vue';
import {useRoute,useRouter} from 'vue-router';
import {api} from '../api';
import {session} from '../session';
import {paginationPath,date} from '../domain';
import {requiresStoredState} from '../recovery';
import {hasPermission,initials,permissionLabels,eventLabels,operatorStatusFilter} from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
import FetchState from '../components/FetchState.vue';
const rows=ref([]),catalogue=ref([]),busy=ref(false),saving=ref(false),error=ref(null),dialogError=ref(null),message=ref('');
const readError=ref(null),unknownAccount=ref(false);
async function reconcileAccount(){await load();if(!readError.value){unknownAccount.value=false;mode.value='';message.value='Daftar akun telah dibaca kembali. Periksa keadaan dan riwayat akun sebelum melakukan perubahan berikutnya.';}}
const route=useRoute(),router=useRouter();
const search=ref(''),mode=ref(''),target=ref(null),history=ref([]),historyLoading=ref(false);let historySequence=0;onBeforeUnmount(()=>{historySequence++;});
const filter=computed({get:()=>operatorStatusFilter(route.query.status),set:value=>router.replace({path:route.path,query:{...route.query,status:operatorStatusFilter(value)||undefined}})});
const form=reactive({full_name:'',email:'',permission_ids:[],reason:''});
const formValid=computed(()=>mode.value==='create'?Boolean(form.full_name.trim()&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())):Boolean(form.reason.trim()));
function grantNames(ids){return (ids||[]).map(id=>{const item=catalogue.value.find(x=>x.id===id);return item?(permissionLabels[item.codename]||item.name):'Izin '+id;}).join(', ')||'Tidak ada izin';}
const state=user=>!user.email_verified_at?'pending':user.is_active?'active':'inactive';
const stateLabel=user=>({pending:'Menunggu aktivasi',active:'Aktif',inactive:'Nonaktif'}[state(user)]);
const visible=computed(()=>rows.value.filter(x=>(!filter.value||state(x)===filter.value)&&(!search.value||[x.full_name,x.email].some(v=>v.toLowerCase().includes(search.value.toLowerCase())))));
async function all(path){const result=[];do{const r=await api(path);result.push(...r.results);path=r.next?paginationPath(r.next):null;}while(path);return result;}
async function load(){busy.value=true;error.value=null;readError.value=null;try{[rows.value,catalogue.value]=await Promise.all([all('admin/operators/?page_size=100'),all('admin/operator-permissions/?page_size=100')]);}catch(e){readError.value=e;rows.value=[];}finally{busy.value=false;}}
function open(kind,user=null){mode.value=kind;target.value=user;dialogError.value=null;Object.assign(form,{full_name:user?.full_name||'',email:user?.email||'',permission_ids:[...(user?.permission_ids||[])],reason:''});}
async function save(){
 if(saving.value)return;saving.value=true;dialogError.value=null;
 try{
  if(mode.value==='create'){
   await api('admin/operators/',{method:'POST',body:{full_name:form.full_name.trim(),email:form.email.trim(),permission_ids:form.permission_ids}});
   message.value='Akun Operator dibuat dan menunggu aktivasi pemilik email. Gunakan Kirim ulang aktivasi bila petunjuk belum diterima.';
  }else{
   const body=mode.value==='permissions'?{full_name:form.full_name.trim(),permission_ids:form.permission_ids,reason:form.reason.trim()}:{is_active:mode.value==='activate',reason:form.reason.trim()};
   await api(`admin/operators/${target.value.id}/`,{method:'PATCH',body});message.value=mode.value==='permissions'?'Izin Operator diperbarui.':'Status akun Operator diperbarui. Riwayat tetap disimpan.';
  }
  mode.value='';await load();
 }catch(e){dialogError.value=e;if(requiresStoredState(e))unknownAccount.value=true;}finally{saving.value=false;}
}
async function resend(user){if(saving.value)return;saving.value=true;error.value=null;message.value='';try{await api(`admin/operators/${user.id}/activation-otp/`,{method:'POST',body:{}});message.value='Petunjuk aktivasi baru disiapkan untuk '+user.full_name+'. Pemilik akun menggunakan tautan dan OTP dari pesan terbaru.';}catch(e){error.value=e;}finally{saving.value=false;}}
async function viewHistory(user){open('history',user);const version=++historySequence;history.value=[];historyLoading.value=true;try{const rows=await all('workspace/audit/?operator_id='+user.id+'&page_size=100');if(version===historySequence&&target.value?.id===user.id)history.value=rows;}catch(e){if(version===historySequence)dialogError.value=e;}finally{if(version===historySequence)historyLoading.value=false;}}
onMounted(load);
</script>
<template>
 <div class="page-heading ws-page-heading"><div><div class="eyebrow">RUANG KERJA ADMIN</div><h1>Manajemen Operator</h1><p class="subtitle">Kelola akun, aktivasi, dan izin petugas dengan riwayat yang tetap terjaga.</p></div><button class="primary" :disabled="busy||saving||Boolean(readError)" @click="open('create')"><AppIcon name="plus" :size="16" />Tambah Operator</button></div>
 <ErrorNotice :error="error" /><p v-if="message" class="notice success" role="status">{{ message }}</p>
 <p v-if="filter" class="ws-quick-filter"><span><AppIcon name="users" :size="17" />{{ {active:'Operator aktif',pending:'Operator menunggu aktivasi',inactive:'Operator nonaktif'}[filter] }}</span><RouterLink to="/workspace/operators">Tampilkan semua Operator<AppIcon name="arrow" :size="15" /></RouterLink></p>
 <section class="card ws-table-panel ws-operator-table"><header class="ws-panel-heading"><div><h2>Akun Operator</h2><p>{{ busy?'Membaca akun…':readError?'Jumlah akun belum tersedia':visible.length+' dari '+rows.length+' akun ditampilkan.' }} Nama petugas mengikuti nama lengkap pada akun.</p></div><button :disabled="busy||saving" @click="load"><AppIcon name="refresh" :size="15" />Muat ulang</button></header>
 <div class="ws-filters"><label class="ws-search"><AppIcon name="search" :size="17" /><span class="sr-only">Cari nama atau email</span><input v-model="search" placeholder="Cari nama atau email"></label><label><span class="sr-only">Status akun</span><select v-model="filter"><option value="">Semua status</option><option value="active">Aktif</option><option value="pending">Menunggu aktivasi</option><option value="inactive">Nonaktif</option></select></label></div>
 <FetchState v-if="busy" compact title="Memuat akun Operator…" description="Membaca akun dan katalog izin." /><FetchState v-else-if="readError" state="error" compact title="Akun Operator belum dapat dimuat" description="Coba lagi untuk membaca akun petugas." :error="readError" :disabled="busy||saving" @retry="load" /><FetchState v-else-if="!visible.length" state="empty" compact title="Belum ada Operator yang sesuai" description="Ubah filter atau tambahkan akun petugas sesuai kewenangan Anda." />
 <div v-if="!busy&&!readError&&visible.length" class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Operator</th><th>Status akun</th><th>Aktivasi email</th><th>Izin</th><th>Aksi</th></tr></thead><tbody><tr v-for="user in visible" :key="user.id"><td><div class="ws-person"><span class="avatar">{{ initials(user.full_name) }}</span><div><strong>{{ user.full_name }}</strong><small>{{ user.email }}</small></div></div></td><td><span class="ws-badge" :class="state(user)==='active'?'tone-success':state(user)==='pending'?'tone-warning':'tone-grey'">{{ stateLabel(user) }}</span></td><td>{{ user.email_verified_at?'Terverifikasi':'Belum diverifikasi' }}</td><td><span>{{ user.permission_ids.length }} izin diberikan</span></td><td class="ws-row-actions"><button class="link" :disabled="saving" @click="open('permissions',user)">Kelola akun & izin</button><button v-if="!user.email_verified_at" class="link" :disabled="saving" @click="resend(user)">Kirim ulang aktivasi</button><button v-else class="link" :disabled="saving" @click="open(user.is_active?'deactivate':'activate',user)">{{ user.is_active?'Nonaktifkan':'Aktifkan kembali' }}</button><button v-if="hasPermission(session.user,'view_audit')" class="link" :disabled="saving" @click="viewHistory(user)">Lihat riwayat</button></td></tr></tbody></table></div>
 </section>
 <p class="fine">Pemilik akun menetapkan kata sandinya sendiri melalui aktivasi email. Akun dan riwayat tidak dihapus saat dinonaktifkan.</p>
 <AppDialog v-if="mode" class="ws-operator-dialog" eyebrow="AKUN OPERATOR" :class="{'is-wide':mode==='create'||mode==='permissions'}" :title="mode==='create'?'Tambah Operator':mode==='permissions'?'Kelola akun dan izin':mode==='history'?'Riwayat akun Operator':mode==='deactivate'?'Nonaktifkan Operator?':'Aktifkan kembali Operator?'" :caption="target?target.full_name+' / '+target.email:'Buat akun petugas dan kirim petunjuk aktivasi.'" @close="!saving&&!unknownAccount&&(mode='')">
  <ErrorNotice v-if="mode!=='history'" :error="dialogError" /><p v-if="unknownAccount" class="notice warning" role="status">Respons perubahan akun belum pasti. Baca akun dan riwayat tersimpan sebelum mencoba lagi. Tidak ada pengiriman ulang otomatis.</p>
  <template v-if="mode==='history'"><FetchState v-if="historyLoading" compact title="Memuat riwayat akun…" /><FetchState v-else-if="dialogError" compact state="error" title="Riwayat akun belum dapat dimuat" description="Coba lagi untuk membaca akun yang sama." :error="dialogError" @retry="viewHistory(target)" /><FetchState v-else-if="!history.length" compact state="empty" title="Belum ada catatan perubahan akun" /><ol v-if="!historyLoading&&!dialogError" class="ws-timeline"><li v-for="event in history" :key="event.id"><strong>{{ eventLabels[event.action]||event.action }}</strong><small>{{ event.actor_name }} · {{ date(event.created_at) }}</small><p v-if="event.after.reason">{{ event.after.reason }}</p><small v-if="event.after.changed_fields?.length">Perubahan: {{ event.after.changed_fields.map(key=>({full_name:'nama lengkap',permission_ids:'izin',is_active:'status akun'}[key]||key)).join(', ') }}</small><details v-if="event.after.changed_fields?.includes('permission_ids')"><summary>Perubahan izin</summary><p>Sebelumnya: {{ grantNames(event.before.permission_ids) }}</p><p>Sesudahnya: {{ grantNames(event.after.permission_ids) }}</p></details></li></ol></template>
  <form v-else id="operator-form" @submit.prevent="save"><fieldset :disabled="saving||unknownAccount">
   <div v-if="mode==='create'||mode==='permissions'" class="ws-operator-form-grid"><div class="ws-operator-identity"><div class="field"><label for="operator-name">Nama lengkap *</label><input id="operator-name" v-model="form.full_name" required maxlength="150" autocomplete="name" :disabled="saving" :readonly="mode==='permissions'"></div><div class="field"><label for="operator-email">Email *</label><input id="operator-email" v-model="form.email" type="email" required maxlength="254" autocomplete="email" :disabled="saving" :readonly="mode==='permissions'"></div><p v-if="mode==='permissions'" class="fine">Nama dan email ditampilkan hanya baca. Pemilik akun mengubah nama melalui Profil.</p></div><fieldset class="ws-permissions"><legend>Izin Operator</legend><div class="ws-permission-options"><label v-for="item in catalogue" :key="item.id" class="check-label"><input v-model="form.permission_ids" type="checkbox" :value="item.id" :disabled="saving">{{ permissionLabels[item.codename]||item.name }}</label></div><small>Izin mengikuti katalog sistem. Akses privat tetap memerlukan penugasan sebagai penanggung jawab.</small></fieldset></div>
   <p v-if="mode==='deactivate'" class="notice warning">Akun akan dinonaktifkan. Tinjau laporan yang masih ditangani dan lakukan pengalihan sesuai kewenangan. Riwayat akun tetap disimpan.</p>
   <div v-if="mode!=='create'" class="field"><label for="operator-reason">Alasan perubahan *</label><textarea id="operator-reason" v-model="form.reason" required maxlength="1500" :disabled="saving" /></div>
   <p v-else class="notice">Setelah akun dibuat, pemilik email menyelesaikan aktivasi dengan OTP dan menetapkan kata sandinya sendiri.</p>
  </fieldset></form>
  <template #actions><button :disabled="saving||unknownAccount" @click="mode=''">{{ mode==='history'?'Tutup':'Batal' }}</button><button v-if="unknownAccount" class="primary" :disabled="busy||saving" @click="reconcileAccount">Periksa akun tersimpan</button><button v-else-if="mode!=='history'" form="operator-form" type="submit" :class="mode==='deactivate'?'danger':'primary'" :disabled="saving||!formValid">{{ saving?'Menyimpan…':mode==='create'?'Buat akun & kirim aktivasi':mode==='permissions'?'Simpan perubahan':mode==='deactivate'?'Nonaktifkan akun':'Aktifkan kembali' }}</button></template>
 </AppDialog>
</template>
