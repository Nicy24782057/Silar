<script setup>
import {computed,onMounted,reactive,ref} from 'vue';
import {useRoute,useRouter} from 'vue-router';
import {api} from '../api';
import {session} from '../session';
import {paginationPath,date} from '../domain';
import {hasPermission,initials,permissionLabels,eventLabels,operatorStatusFilter} from '../workspace';
import AppIcon from '../components/AppIcon.vue';
import AppDialog from '../components/AppDialog.vue';
import ErrorNotice from '../components/ErrorNotice.vue';
const rows=ref([]),catalogue=ref([]),busy=ref(false),saving=ref(false),error=ref(null),dialogError=ref(null),message=ref('');
const route=useRoute(),router=useRouter();
const search=ref(''),mode=ref(''),target=ref(null),history=ref([]),historyLoading=ref(false);
const filter=computed({get:()=>operatorStatusFilter(route.query.status),set:value=>router.replace({path:route.path,query:{...route.query,status:operatorStatusFilter(value)||undefined}})});
const form=reactive({full_name:'',email:'',permission_ids:[],reason:''});
function grantNames(ids){return (ids||[]).map(id=>{const item=catalogue.value.find(x=>x.id===id);return item?(permissionLabels[item.codename]||item.name):'Izin '+id;}).join(', ')||'Tidak ada izin';}
const state=user=>!user.email_verified_at?'pending':user.is_active?'active':'inactive';
const stateLabel=user=>({pending:'Menunggu aktivasi',active:'Aktif',inactive:'Nonaktif'}[state(user)]);
const visible=computed(()=>rows.value.filter(x=>(!filter.value||state(x)===filter.value)&&(!search.value||[x.full_name,x.email].some(v=>v.toLowerCase().includes(search.value.toLowerCase())))));
async function all(path){const result=[];do{const r=await api(path);result.push(...r.results);path=r.next?paginationPath(r.next):null;}while(path);return result;}
async function load(){busy.value=true;error.value=null;try{[rows.value,catalogue.value]=await Promise.all([all('admin/operators/?page_size=100'),all('admin/operator-permissions/?page_size=100')]);}catch(e){error.value=e;rows.value=[];}finally{busy.value=false;}}
function open(kind,user=null){mode.value=kind;target.value=user;dialogError.value=null;Object.assign(form,{full_name:user?.full_name||'',email:user?.email||'',permission_ids:[...(user?.permission_ids||[])],reason:''});}
async function save(){
 if(saving.value)return;saving.value=true;dialogError.value=null;
 try{
  if(mode.value==='create'){
   await api('admin/operators/',{method:'POST',body:{full_name:form.full_name.trim(),email:form.email.trim(),permission_ids:form.permission_ids}});
   message.value='Akun Operator dibuat dan menunggu aktivasi pemilik email. Gunakan Kirim ulang aktivasi bila petunjuk belum diterima.';
  }else{
   const body=mode.value==='permissions'?{full_name:form.full_name.trim(),permission_ids:form.permission_ids,reason:form.reason.trim()}:{is_active:mode.value==='activate',reason:form.reason.trim()};
   await api(`admin/operators/${target.value.id}/`,{method:'PATCH',body});message.value=mode.value==='permissions'?'Nama dan izin Operator diperbarui.':'Status akun Operator diperbarui. Riwayat tetap disimpan.';
  }
  mode.value='';await load();
 }catch(e){dialogError.value=e;}finally{saving.value=false;}
}
async function resend(user){if(saving.value)return;saving.value=true;error.value=null;message.value='';try{await api(`admin/operators/${user.id}/activation-otp/`,{method:'POST',body:{}});message.value='Petunjuk aktivasi baru disiapkan untuk '+user.full_name+'. Pemilik akun menggunakan tautan dan OTP dari pesan terbaru.';}catch(e){error.value=e;}finally{saving.value=false;}}
async function viewHistory(user){open('history',user);history.value=[];historyLoading.value=true;try{history.value=await all('workspace/audit/?operator_id='+user.id+'&page_size=100');}catch(e){dialogError.value=e;}finally{historyLoading.value=false;}}
onMounted(load);
</script>
<template>
 <div class="page-heading ws-page-heading"><div><div class="eyebrow">RUANG KERJA ADMIN</div><h1>Manajemen Operator</h1><p class="subtitle">Kelola akun, aktivasi, dan izin petugas dengan riwayat yang tetap terjaga.</p></div><button class="primary" :disabled="busy||saving" @click="open('create')"><AppIcon name="plus" :size="16" />Tambah Operator</button></div>
 <ErrorNotice :error="error" /><p v-if="message" class="notice success" role="status">{{ message }}</p>
 <p v-if="filter" class="ws-quick-filter"><span><AppIcon name="users" :size="17" />{{ {active:'Operator aktif',pending:'Operator menunggu aktivasi',inactive:'Operator nonaktif'}[filter] }}</span><RouterLink to="/workspace/operators">Tampilkan semua Operator<AppIcon name="arrow" :size="15" /></RouterLink></p>
 <section class="card ws-table-panel"><header class="ws-panel-heading"><div><h2>Akun Operator</h2><p>{{ visible.length }} dari {{ rows.length }} akun ditampilkan. Nama petugas mengikuti nama lengkap pada akun.</p></div><button :disabled="busy||saving" @click="load"><AppIcon name="refresh" :size="15" />Muat ulang</button></header>
 <div class="ws-filters"><label class="ws-search"><AppIcon name="search" :size="17" /><span class="sr-only">Cari nama atau email</span><input v-model="search" placeholder="Cari nama atau email"></label><label><span class="sr-only">Status akun</span><select v-model="filter"><option value="">Semua status</option><option value="active">Aktif</option><option value="pending">Menunggu aktivasi</option><option value="inactive">Nonaktif</option></select></label></div>
 <p v-if="busy" class="ws-loading" role="status">Membaca akun Operator…</p><div v-if="!busy&&!visible.length" class="empty"><AppIcon name="users" :size="36" /><h3>Belum ada Operator yang sesuai</h3><p>Tambahkan akun petugas, lalu minta pemilik email menyelesaikan aktivasi.</p></div>
 <div v-if="visible.length" class="ws-table-scroll"><table class="ws-table"><thead><tr><th>Operator</th><th>Status akun</th><th>Aktivasi email</th><th>Izin</th><th>Aksi</th></tr></thead><tbody><tr v-for="user in visible" :key="user.id"><td><div class="ws-person"><span class="avatar">{{ initials(user.full_name) }}</span><div><strong>{{ user.full_name }}</strong><small>{{ user.email }}</small></div></div></td><td><span class="ws-badge" :class="state(user)==='active'?'tone-success':state(user)==='pending'?'tone-warning':'tone-grey'">{{ stateLabel(user) }}</span></td><td>{{ user.email_verified_at?'Terverifikasi':'Belum diverifikasi' }}</td><td><span>{{ user.permission_ids.length }} izin diberikan</span></td><td class="ws-row-actions"><button class="link" :disabled="saving" @click="open('permissions',user)">Kelola akun & izin</button><button v-if="!user.email_verified_at" class="link" :disabled="saving" @click="resend(user)">Kirim ulang aktivasi</button><button v-else class="link" :disabled="saving" @click="open(user.is_active?'deactivate':'activate',user)">{{ user.is_active?'Nonaktifkan':'Aktifkan kembali' }}</button><button v-if="hasPermission(session.user,'view_audit')" class="link" :disabled="saving" @click="viewHistory(user)">Lihat riwayat</button></td></tr></tbody></table></div>
 </section>
 <p class="fine">Pemilik akun menetapkan kata sandinya sendiri melalui aktivasi email. Akun dan riwayat tidak dihapus saat dinonaktifkan.</p>
 <AppDialog v-if="mode" :title="mode==='create'?'Tambah Operator':mode==='permissions'?'Kelola akun dan izin':mode==='history'?'Riwayat akun Operator':mode==='deactivate'?'Nonaktifkan Operator?':'Aktifkan kembali Operator?'" :caption="target?target.full_name+' / '+target.email:'Buat akun petugas dan kirim petunjuk aktivasi.'" @close="!saving&&(mode='')">
  <ErrorNotice :error="dialogError" />
  <template v-if="mode==='history'"><p v-if="historyLoading" role="status">Membaca riwayat…</p><p v-else-if="!history.length" class="muted">Belum ada catatan yang dapat ditampilkan.</p><ol class="ws-timeline"><li v-for="event in history" :key="event.id"><strong>{{ eventLabels[event.action]||event.action }}</strong><small>{{ event.actor_name }} · {{ date(event.created_at) }}</small><p v-if="event.after.reason">{{ event.after.reason }}</p><small v-if="event.after.changed_fields?.length">Perubahan: {{ event.after.changed_fields.map(key=>({full_name:'nama lengkap',permission_ids:'izin',is_active:'status akun'}[key]||key)).join(', ') }}</small><details v-if="event.after.changed_fields?.includes('permission_ids')"><summary>Perubahan izin</summary><p>Sebelumnya: {{ grantNames(event.before.permission_ids) }}</p><p>Sesudahnya: {{ grantNames(event.after.permission_ids) }}</p></details></li></ol></template>
  <form v-else id="operator-form" @submit.prevent="save">
   <template v-if="mode==='create'||mode==='permissions'"><div class="field"><label for="operator-name">Nama lengkap *</label><input id="operator-name" v-model="form.full_name" required maxlength="150" autocomplete="name" :disabled="saving"></div><div v-if="mode==='create'" class="field"><label for="operator-email">Email *</label><input id="operator-email" v-model="form.email" type="email" required maxlength="254" autocomplete="email" :disabled="saving"></div><fieldset class="ws-permissions"><legend>Izin Operator</legend><label v-for="item in catalogue" :key="item.id" class="check-label"><input v-model="form.permission_ids" type="checkbox" :value="item.id" :disabled="saving">{{ permissionLabels[item.codename]||item.name }}</label><small>Izin mengikuti katalog sistem. Akses privat tetap memerlukan penugasan sebagai penanggung jawab.</small></fieldset></template>
   <p v-if="mode==='deactivate'" class="notice warning">Akun akan dinonaktifkan. Tinjau laporan yang masih ditangani dan lakukan pengalihan sesuai kewenangan. Riwayat akun tetap disimpan.</p>
   <div v-if="mode!=='create'" class="field"><label for="operator-reason">Alasan perubahan *</label><textarea id="operator-reason" v-model="form.reason" required maxlength="1500" :disabled="saving" /></div>
   <p v-else class="notice">Setelah akun dibuat, pemilik email menyelesaikan aktivasi dengan OTP dan menetapkan kata sandinya sendiri.</p>
  </form>
  <template #actions><button :disabled="saving" @click="mode=''">{{ mode==='history'?'Tutup':'Batal' }}</button><button v-if="mode!=='history'" form="operator-form" type="submit" :class="mode==='deactivate'?'danger':'primary'" :disabled="saving">{{ saving?'Menyimpan…':mode==='create'?'Buat akun & kirim aktivasi':mode==='permissions'?'Simpan perubahan':mode==='deactivate'?'Nonaktifkan akun':'Aktifkan kembali' }}</button></template>
 </AppDialog>
</template>
