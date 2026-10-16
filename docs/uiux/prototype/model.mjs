export const demoLogin=Object.freeze({email:'pelapor@contoh.test',password:'Silar123!'});
export const story='Banjir di Jalan Melati sejak pagi. Air masuk ke beberapa rumah. Saya belum mengetahui kondisi korban.';
export const uid=n=>`00000000-0000-4000-8000-${String(n).padStart(12,'0')}`;
export const operatorPermissions=['view_queue','view_assigned_report','claim_report','review_report','manage_followup','publish_report','close_report'];
const clone=o=>structuredClone(o);
export function problem(code,message){const e=new Error(message);e.code=code;throw e;}
const ensure=(ok,code,msg)=>{if(!ok)problem(code,msg);};
const base=(n,official=false)=>({id:uid(n),owner:'reporter',createdAt:'16 Okt 2026, 08.30 WIB',submittedAt:official?'16 Okt 2026, 09.00 WIB':null,revision:1,inputRevision:1,preparation:official?'READY':'DRAFT',workflow:official?'SUBMITTED':'NOT_SUBMITTED',validation:'NOT_REVIEWED',publication:'NOT_DECIDED',text:official?story:'',savedText:official?story:'',pendingFiles:[],evidence:[],selected:[],bundle:null,bundles:[],run:null,card:official?{version:1,category:'FLOOD',confidence:.73,uncertain:false,reasons:[],narrative:story,location:'Jalan Melati',time:'Sejak pagi',impact:'Air masuk ke beberapa rumah',victims:'',parties:'',objects:'Rumah',occurredAt:''}:null,confirmed:official?1:null,officialVersion:official?1:null,assignee:null,assignmentReason:null,review:null,followups:[],candidate:null,publicVersion:null,publicVersions:[],publicationSequence:0,history:[],clientLost:false});
export function initial(){
 const a=base(1),b=base(2,true),c=base(3,true),d=base(4,true);
 c.owner='other';c.assignee='op-a';c.workflow='ASSIGNED';c.card.category='FIRE';c.card.narrative='Kebakaran dilaporkan di kawasan pasar. Petugas melakukan penanganan.';
 d.owner='other';d.assignee='op-b';d.workflow='CLOSED';d.validation='VALID';d.publication='PUBLISHED';d.review={outcome:'VALID',reason:'Catatan pemeriksaan internal contoh.'};d.publicationSequence=1;
 d.publicVersion={version:1,state:'PUBLISHED',publishedOrder:1,data:{event_type:'FLOOD',summary:'Banjir dilaporkan di kawasan permukiman. Informasi ditinjau berdasarkan laporan yang tersedia.',general_location:'Kawasan Melati',time_text:'Pagi hari',general_impact:'Sebagian rumah terdampak.',handling_update:'Penanganan telah dicatat.',occurred_at:null},publishedAt:'16 Okt 2026, 09.20 WIB'};d.publicVersions=[clone(d.publicVersion)];
 return {role:'reporter',operator:'op-a',page:'RP01',selectedId:a.id,reports:[a,b,c,d],operators:[{id:'op-a',name:'Operator A',email:'operator-a@contoh.test',active:true,verified:true,permissions:[...operatorPermissions]},{id:'op-b',name:'Operator B',email:'operator-b@contoh.test',active:true,verified:true,permissions:[...operatorPermissions]},{id:'op-new',name:'Operator Baru',email:'operator-baru@contoh.test',active:false,verified:false,permissions:[...operatorPermissions]}],scenario:'NORMAL',offline:false,adminPrivate:false,notificationRead:[],notifications:[{id:1,role:'reporter',reportId:b.id,message:'Laporan Anda berhasil dikirim.',kind:'SUBMITTED'},{id:2,role:'operator',operator:'op-a',reportId:c.id,message:'Anda menerima penugasan laporan.',kind:'ASSIGNED'}],notice:null,nextId:100,nextPublicationOrder:2,accountPurpose:'EMAIL_VERIFICATION',accountMessage:null,accountName:'Pelapor Contoh',accountEmail:demoLogin.email,demoAccounts:{[demoLogin.email]:{password:demoLogin.password,name:'Pelapor Contoh',verified:true}},demoChallenge:null,emailDemo:false,publicationChecked:false,reviewOutcome:'VALID',reviewReason:'',publicDraft:null,otpResent:false,resendSeconds:0};
}
export const current=s=>s.reports.find(r=>r.id===s.selectedId);
export const permitted=(s,p)=>{const a=s.operators.find(o=>o.id===s.operator);return !!(s.role==='operator'&&a?.active&&a.verified&&a.permissions.includes(p));};
export function readable(s,r){if(s.role==='reporter')return r.owner==='reporter';if(s.role==='operator')return permitted(s,'view_assigned_report')&&r.workflow!=='NOT_SUBMITTED'&&r.assignee===s.operator;if(s.role==='admin')return r.workflow!=='NOT_SUBMITTED';return !!r.publicVersion;}
export function fullReadable(s,r){return readable(s,r)&&(s.role!=='admin'||s.adminPrivate);}
export const writable=(s,r)=>permitted(s,'view_assigned_report')&&r.assignee===s.operator&&r.workflow!=='CLOSED';
export function notice(s,message,type='success',code=''){s.notice={message,type,code};}
function log(r,action){r.history.push({action,revision:r.revision,at:'Baru saja · simulasi'});}
function touch(r,action){r.revision++;log(r,action);}
function notify(s,role,r,message,kind,operator=null){s.notifications.unshift({id:s.nextId++,role,operator,reportId:r.id,message,kind});}
function owner(s,r){ensure(s.role==='reporter'&&r.owner==='reporter','NOT_FOUND','Laporan tidak tersedia untuk akun ini.');ensure(r.workflow==='NOT_SUBMITTED','TRANSITION_REJECTED','Versi resmi sudah dikirim dan tidak dapat disunting.');}
function handler(s,r){ensure(writable(s,r),'PERMISSION_DENIED','Tindakan memerlukan Operator penanggung jawab dan laporan yang masih terbuka.');}
function online(s){ensure(!s.offline,'OFFLINE','Sambungkan internet untuk melanjutkan. Perubahan belum tersimpan ke server.');}
function activateSource(r){r.inputRevision++;r.card=null;r.confirmed=null;r.preparation='DRAFT';}
export function act(s,action,p={}){
 const r=current(s);
 const permission={CLAIM:'claim_report',REVIEW:'review_report',FOLLOWUP:'manage_followup',FINISH_FOLLOWUP:'manage_followup',DECISION:'publish_report',CREATE_CANDIDATE:'publish_report',APPROVE:'publish_report',PUBLISH:'publish_report',CANCEL_CANDIDATE:'publish_report',CLOSE:'close_report'}[action];
 if(permission)ensure(permitted(s,permission),'PERMISSION_DENIED','Akun tidak aktif atau tidak memiliki izin tindakan ini.');
 if(s.scenario==='REVISION_CONFLICT'&&['SAVE','CONFIRM','SUBMIT','REVIEW','DECISION','CREATE_CANDIDATE','CLOSE'].includes(action)){s.scenario='NORMAL';r.revision++;problem('REVISION_CONFLICT','Laporan berubah pada sesi lain. Detail terbaru dimuat; periksa kembali sebelum mengulangi tindakan.');}
 if(action==='ROLE'){s.role=p.role;s.page={reporter:'RP01',operator:'OP01',admin:'AD02',public:'PB01',account:'AK01'}[p.role];s.notice=null;return;}
 if(action==='NAV'){s.page=p.page;s.notice=null;if(p.id)s.selectedId=p.id;return;}
 if(action==='SCENARIO'){s.scenario=p.value;s.offline=p.value==='OFFLINE';s.notice=null;return;}
 if(action==='TEXT'){owner(s,r);r.text=p.value;return;}
 if(action==='SAMPLE'){owner(s,r);r.text=story;notice(s,'Cerita contoh dimasukkan. Simpan Draft untuk menyimpan sumber.');return;}
 if(action==='ADD_FILE'){owner(s,r);r.pendingFiles.push({id:uid(s.nextId++),type:p.type,name:p.name,mime:p.mime,size:p.size,preview:p.preview||null});return;}
 if(action==='SELECT'){owner(s,r);if(p.checked){const item=r.evidence.find(e=>e.id===p.id);if(item?.type!=='IMAGE')r.selected=r.selected.filter(id=>r.evidence.find(e=>e.id===id)?.type!==item.type);r.selected.push(p.id);}else r.selected=r.selected.filter(id=>id!==p.id);return;}
 if(action==='SAVE'){
  online(s);owner(s,r);if(s.scenario==='INVALID_MEDIA')problem('MEDIA_UNSUPPORTED','Berkas contoh tidak dapat diterima. Pilih berkas yang didukung.');
  const changed=r.text.trim()!==r.savedText||r.pendingFiles.length||!r.bundle||JSON.stringify(r.selected)!==JSON.stringify(r.bundle?.items);
  ensure(r.text.trim()||r.pendingFiles.length||r.selected.length,'INVALID_PAYLOAD','Tambahkan teks, audio, atau gambar sebelum menyimpan sumber.');
  if(!changed){notice(s,'Draft sudah tersimpan; tidak ada perubahan sumber baru.');return;}
  if(r.text.trim()!==r.savedText){if(r.text.trim()){const item={id:uid(s.nextId++),type:'TEXT',name:'Teks laporan',text:r.text.trim()};r.evidence.push(item);r.selected=r.selected.filter(id=>r.evidence.find(e=>e.id===id)?.type!=='TEXT');r.selected.push(item.id);}else r.selected=r.selected.filter(id=>r.evidence.find(e=>e.id===id)?.type!=='TEXT');r.savedText=r.text.trim();}
  for(const item of r.pendingFiles){if(item.type==='AUDIO')r.selected=r.selected.filter(id=>r.evidence.find(e=>e.id===id)?.type!=='AUDIO');r.evidence.push(item);r.selected.push(item.id);}r.pendingFiles=[];
  ensure(r.selected.length,'INVALID_PAYLOAD','Pilih setidaknya satu bukti untuk sumber analisis.');
  r.bundle={version:r.bundles.length+1,items:[...r.selected]};r.bundles.push(clone(r.bundle));r.correctedNarrative=null;activateSource(r);touch(r,'Bukti dan pilihan sumber disimpan sebagai bundle baru');notice(s,'Draft tersimpan dalam simulasi. Sumber siap dianalisis.');return;
 }
 if(action==='ANALYSE'){
  online(s);owner(s,r);ensure(!['RUNNING','UNKNOWN'].includes(r.run?.status),'REQUEST_'+r.run?.status,'Proses sebelumnya belum memiliki hasil terminal. Periksa status terlebih dahulu.');
  ensure(r.bundle&&r.bundle.items.length,'INVALID_PAYLOAD','Simpan dan pilih bukti sebelum analisis.');
  ensure(r.text.trim()===r.savedText&&!r.pendingFiles.length&&JSON.stringify(r.selected)===JSON.stringify(r.bundle.items),'INPUT_CHANGED','Ada perubahan sumber yang belum disimpan. Pilih Simpan Draft terlebih dahulu.');
  if(s.scenario==='CAPACITY_BUSY')problem('CAPACITY_BUSY','Kapasitas pemrosesan sedang penuh. Coba lagi secara manual setelah kapasitas tersedia.');
  if(s.scenario==='CONFIG_NOT_READY')problem('AI_CONFIGURATION_NOT_READY','Layanan analisis belum siap. Coba kembali setelah konfigurasi tersedia.');
  r.preparation='PROCESSING';r.card=null;r.confirmed=null;r.run={status:s.scenario==='UNKNOWN'?'UNKNOWN':'RUNNING',inputRevision:r.inputRevision,scenario:s.scenario,id:uid(s.nextId++),stage:'NARRATIVE',error:null};touch(r,'Analisis contoh dimulai');s.page='RP03';s.notice=null;return;
 }
 if(action==='FINISH'){
  ensure(r.run&&['RUNNING','UNKNOWN'].includes(r.run.status),'TRANSITION_REJECTED','Tidak ada proses aktif.');
  if(r.run.inputRevision!==r.inputRevision){r.run.status='FAILED';r.run.error='INPUT_CHANGED';touch(r,'Hasil sumber lama tidak diaktifkan');notice(s,'Sumber berubah selama proses. Periksa sumber terbaru sebelum analisis ulang.','error','INPUT_CHANGED');return;}
  const sc=r.run.scenario,none=sc==='NON_EVENT';
  r.run.status='SUCCEEDED';r.run.stage='PERSIST';r.preparation=none?'BLOCKED':'AWAITING_CONFIRMATION';
  const narrative=(r.run.mode==='NARRATIVE_REVISION'?r.correctedNarrative:r.savedText)||'Narasi contoh dari kanal yang dipilih. Periksa kesesuaiannya dengan bukti.',isSample=narrative===story;
  r.card={version:(r.cardSequence||0)+1,category:none?null:'FLOOD',confidence:sc==='UNCERTAIN'?.48:.73,uncertain:sc==='UNCERTAIN',reasons:sc==='UNCERTAIN'?['LOW_CLASSIFICATION_CONFIDENCE']:[],narrative,location:isSample?'Jalan Melati':'',time:isSample?'Sejak pagi':'',impact:isSample?'Air masuk ke beberapa rumah':'',victims:'',parties:'',objects:isSample?'Rumah':'',occurredAt:''};r.cardSequence=r.card.version;
  r.clientLost=sc==='LOST_RESPONSE';touch(r,'Hasil analisis contoh tersimpan');if(!r.clientLost)s.page='RP04';return;
 }
 if(action==='READ_STATUS'){online(s);ensure(r.run,'NOT_FOUND','Belum ada rekaman proses untuk laporan ini.');if(r.run.status==='SUCCEEDED'){r.clientLost=false;s.page='RP04';notice(s,'Hasil tersimpan ditemukan. Analisis tidak dijalankan ulang.');}else if(r.run.status==='FAILED')notice(s,'Proses tercatat gagal: '+r.run.error+'. Periksa penyebab sebelum mencoba lagi.','error',r.run.error);else notice(s,r.run.status==='UNKNOWN'?'Hasil proses belum dapat dipastikan. Analisis baru ditahan sampai pemulihan teknis selesai.':'Rekaman contoh menunjukkan proses masih berjalan.','info',r.run.status);return;}
 if(action==='TECH_RECOVER'){ensure(r.run&&['RUNNING','UNKNOWN'].includes(r.run.status),'TRANSITION_REJECTED','Tidak ada proses yang perlu dipulihkan.');r.run.status='FAILED';r.run.error='RECOVERY_ABORTED';if(r.run.inputRevision===r.inputRevision)r.preparation='FAILED';touch(r,'Simulasi pengelola teknis membuktikan proses berhenti dan mengesahkan pemulihan');notice(s,'Simulasi pemulihan teknis selesai. Reporter dapat mencoba ulang secara eksplisit.','info');return;}
 if(action==='REVISE_NARRATIVE'){online(s);owner(s,r);ensure(p.text.trim(),'INVALID_PAYLOAD','Narasi tidak boleh kosong.');r.correctedNarrative=p.text;activateSource(r);touch(r,'Revisi narasi tersimpan; analisis SENA/NARA/Fusion diperlukan');s.page='RP03';notice(s,'Narasi direvisi. Analisis ulang diperlukan; konfirmasi lama tidak berlaku.','info');return;}
 if(action==='ANALYSE_REVISION'){owner(s,r);ensure(r.correctedNarrative,'INVALID_PAYLOAD','Belum ada narasi revisi.');const old=r.text;r.text=r.savedText;act(s,'ANALYSE');r.text=old;r.run.mode='NARRATIVE_REVISION';return;}
 if(action==='REVISE_FIELDS'){online(s);owner(s,r);ensure(r.card,'NOT_FOUND','Kartu aktif belum tersedia.');const c=clone(r.card);for(const k of ['location','time','impact','victims','parties','objects','occurredAt'])if(k in p)c[k]=p[k];c.version=++r.cardSequence;r.card=c;r.confirmed=null;r.preparation=c.category?'AWAITING_CONFIRMATION':'BLOCKED';touch(r,'Koreksi field menjadi versi kartu baru');notice(s,'Koreksi tersimpan sebagai versi baru. Periksa dan konfirmasi kembali.');return;}
 if(action==='CONFIRM'){online(s);owner(s,r);ensure(r.card?.category,'NON_EVENT_BLOCKED','Hasil NON_EVENT perlu koreksi narasi dan analisis ulang sebelum konfirmasi.');ensure(!['RUNNING','UNKNOWN'].includes(r.run?.status),'REQUEST_RUNNING','Tunggu hasil proses yang pasti.');r.confirmed=r.card.version;r.preparation='READY';touch(r,'Reporter mengonfirmasi versi aktif');notice(s,'Versi aktif dikonfirmasi. Laporan belum dikirim.');return;}
 if(action==='SUBMIT'){online(s);owner(s,r);ensure(r.card?.category,'NON_EVENT_BLOCKED','NON_EVENT tidak dapat dikirim.');ensure(r.confirmed===r.card.version,'VERSION_NOT_CONFIRMED','Konfirmasi versi aktif sebelum mengirim.');r.officialVersion=r.card.version;r.workflow='SUBMITTED';r.submittedAt='Baru saja · simulasi';touch(r,'Laporan resmi dikirim dan dikunci');notify(s,'reporter',r,'Laporan Anda berhasil dikirim.','SUBMITTED');s.page='RP05';notice(s,'Laporan contoh berhasil dikirim. Versi resmi kini terkunci.');return;}
 if(action==='CLAIM'){online(s);ensure(permitted(s,'view_queue')&&permitted(s,'view_assigned_report'),'PERMISSION_DENIED','Tindakan memerlukan izin antrean dan baca tugas.');if(s.scenario==='CLAIM_CONFLICT'&&!r.assignee){r.assignee=s.operator==='op-a'?'op-b':'op-a';r.workflow='ASSIGNED';problem('CLAIM_CONFLICT','Laporan sudah diambil Operator lain. Antrean telah diperbarui.');}ensure(!r.assignee&&r.workflow==='SUBMITTED','CLAIM_CONFLICT','Laporan tidak lagi tersedia untuk diklaim.');r.assignee=s.operator;r.workflow='ASSIGNED';touch(r,'Laporan diklaim Operator');s.page='OP03';notice(s,'Laporan masuk ke penanganan Anda.');return;}
 if(action==='REVIEW'){online(s);handler(s,r);ensure(!r.publicVersion,'TRANSITION_REJECTED','Hasil review dikunci setelah publikasi pertama.');ensure(p.reason?.trim(),'INVALID_PAYLOAD','Alasan pemeriksaan wajib diisi.');ensure(!r.candidate||p.outcome==='VALID','TRANSITION_REJECTED','Batalkan kandidat aktif sebelum menetapkan hasil ini.');r.validation=p.outcome;r.review={outcome:p.outcome,reason:p.reason};if(r.workflow!=='FOLLOW_UP')r.workflow='IN_REVIEW';if(p.outcome!=='VALID')r.publication='INTERNAL';touch(r,'Operator mencatat pemeriksaan');notify(s,'reporter',r,'Hasil pemeriksaan laporan diperbarui.','REVIEWED');notice(s,'Hasil pemeriksaan tercatat.');return;}
 if(action==='FOLLOWUP'){online(s);handler(s,r);ensure(r.review,'TRANSITION_REJECTED','Catat hasil pemeriksaan terlebih dahulu.');ensure(p.description?.trim(),'INVALID_PAYLOAD','Isi tindak lanjut.');r.followups.push({id:s.nextId++,description:p.description,status:'PENDING'});r.workflow='FOLLOW_UP';touch(r,'Tindak lanjut dicatat');notice(s,'Tindak lanjut berstatus belum selesai.');return;}
 if(action==='FINISH_FOLLOWUP'){online(s);handler(s,r);const f=r.followups.find(f=>f.id===p.id);ensure(f?.status==='PENDING','TRANSITION_REJECTED','Tindak lanjut sudah memiliki hasil akhir.');ensure(p.status!=='CANCELLED'||p.reason?.trim(),'INVALID_PAYLOAD','Alasan pembatalan wajib diisi.');f.status=p.status;f.completionReason=p.reason||'';touch(r,'Status tindak lanjut diperbarui');return;}
 if(action==='DECISION'){online(s);handler(s,r);ensure(r.review,'TRANSITION_REJECTED','Catat hasil pemeriksaan terlebih dahulu.');ensure(p.reason?.trim(),'INVALID_PAYLOAD','Alasan keputusan wajib diisi.');ensure(!r.candidate,'TRANSITION_REJECTED','Batalkan kandidat aktif sebelum mengubah arah publikasi.');if(p.decision==='INTERNAL'){ensure(!r.publicVersion,'TRANSITION_REJECTED','Versi yang sudah terbit tidak ditarik melalui keputusan internal.');r.publication='INTERNAL';}else{ensure(r.validation==='VALID','TRANSITION_REJECTED','Persiapan publikasi memerlukan review VALID.');r.publication='PENDING_APPROVAL';s.page='OP05';}touch(r,'Arah publikasi dicatat');notice(s,p.decision==='INTERNAL'?'Laporan ditetapkan tetap internal.':'Arah publikasi dicatat. Kandidat belum dibuat.');return;}
 if(action==='CREATE_CANDIDATE'){online(s);handler(s,r);ensure(r.validation==='VALID'&&r.publication==='PENDING_APPROVAL'&&!r.candidate,'TRANSITION_REJECTED','Persiapan kandidat belum memenuhi syarat.');ensure(p.data?.summary?.trim(),'INVALID_PAYLOAD','Ringkasan publik wajib diisi.');ensure(Object.keys(p.data).every(k=>['summary','general_location','time_text','general_impact','handling_update','occurred_at'].includes(k)),'INVALID_PAYLOAD','Kandidat hanya menerima field publik yang diizinkan.');r.candidate={version:++r.publicationSequence,state:'DRAFT',data:{...p.data,event_type:r.card.category}};s.publicationChecked=false;touch(r,'Kandidat publikasi baru dibuat');notice(s,'Kandidat tersimpan. Periksa isi dan sanitasi sebelum persetujuan.');return;}
 if(action==='APPROVE'){online(s);handler(s,r);ensure(r.validation==='VALID'&&r.candidate?.state==='DRAFT','TRANSITION_REJECTED','Tidak ada kandidat DRAFT yang dapat disetujui.');ensure(s.publicationChecked,'INVALID_PAYLOAD','Selesaikan pemeriksaan sanitasi versi kandidat.');r.candidate.state='APPROVED';r.publication='APPROVED';touch(r,'Kandidat versi tepat disetujui');notice(s,'Kandidat disetujui. Informasi belum diterbitkan.');return;}
 if(action==='PUBLISH'){online(s);handler(s,r);ensure(r.candidate?.state==='APPROVED'&&r.validation==='VALID','TRANSITION_REJECTED','Setujui kandidat aktif sebelum penerbitan.');r.candidate.state='PUBLISHED';r.candidate.publishedAt='Baru saja · simulasi';r.candidate.publishedOrder=s.nextPublicationOrder++;r.publicVersion=clone(r.candidate);r.publicVersions.push(clone(r.candidate));r.candidate=null;r.publication='PUBLISHED';touch(r,'Versi publik diterbitkan');notify(s,'reporter',r,'Informasi umum laporan diterbitkan.','PUBLISHED');notice(s,'Versi publik contoh diterbitkan. Penanganan belum otomatis ditutup.');return;}
 if(action==='CANCEL_CANDIDATE'){online(s);handler(s,r);ensure(r.candidate&&['DRAFT','APPROVED'].includes(r.candidate.state),'TRANSITION_REJECTED','Hanya kandidat aktif yang dapat dibatalkan.');ensure(p.reason?.trim(),'INVALID_PAYLOAD','Alasan pembatalan wajib diisi.');r.publicVersions.push({...clone(r.candidate),state:'CANCELLED',reason:p.reason});r.candidate=null;r.publication=r.publicVersion?'PUBLISHED':'NOT_DECIDED';touch(r,'Kandidat dibatalkan tanpa menarik versi terbit');notice(s,'Kandidat dibatalkan. Versi terbit sebelumnya tetap tersedia jika ada.');return;}
 if(action==='CLOSE'){online(s);handler(s,r);ensure(r.review&&!r.followups.some(f=>f.status==='PENDING')&&['INTERNAL','PUBLISHED'].includes(r.publication)&&!r.candidate,'TRANSITION_REJECTED','Penutupan memerlukan review, tindak lanjut selesai/dibatalkan, keputusan publikasi final, dan tanpa kandidat aktif.');ensure(p.note?.trim(),'INVALID_PAYLOAD','Catatan penutupan wajib diisi.');r.workflow='CLOSED';touch(r,'Laporan ditutup');notify(s,'reporter',r,'Penanganan laporan ditutup.','CLOSED');notice(s,'Laporan ditutup. Riwayat tetap dapat dibaca.');return;}
 if(action==='ASSIGN'){online(s);ensure(s.role==='admin'&&r.workflow!=='NOT_SUBMITTED'&&r.workflow!=='CLOSED','PERMISSION_DENIED','Penugasan hanya untuk laporan resmi yang belum ditutup.');ensure(p.reason?.trim(),'INVALID_PAYLOAD','Alasan penugasan atau pengalihan wajib diisi.');const target=s.operators.find(o=>o.id===p.operator);ensure(target?.active&&target.verified&&target.permissions.includes('view_assigned_report'),'TRANSITION_REJECTED','Akun tujuan harus aktif, terverifikasi, dan berizin baca tugas.');r.assignee=p.operator;r.assignmentReason=p.reason;if(r.workflow==='SUBMITTED')r.workflow='ASSIGNED';touch(r,'Admin mencatat penugasan atau pengalihan');notify(s,'operator',r,'Anda menerima penugasan laporan.','ASSIGNED',p.operator);notice(s,'Penugasan tersimpan. Akses Operator sebelumnya dicabut.');return;}
 if(action==='AUTH'){
  online(s);const purpose=s.page,email=String(p.email||'').trim().toLowerCase();
  if(['AK03','AK04','AK06'].includes(purpose)){ensure(s.scenario!=='OTP_EXPIRED','OTP_EXPIRED','Kode kedaluwarsa atau tidak dapat digunakan. Ikuti petunjuk pengiriman ulang.');ensure(p.code==='123456'&&s.scenario!=='OTP_INVALID','OTP_INVALID','Kode tidak dapat digunakan. Periksa kembali email terbaru.');}
  if(['AK02','AK04','AK06'].includes(purpose)){ensure(p.password?.length>=8&&p.password===p.password_confirm,'INVALID_PAYLOAD','Gunakan password contoh minimal 8 karakter dengan konfirmasi yang sama. Validator produksi mengikuti backend.');}
  if(purpose==='AK01'){
   ensure(email&&p.password,'INVALID_PAYLOAD','Isi email dan password contoh.');
   const account=s.demoAccounts[email];
   ensure(account&&account.password===p.password&&account.verified,'INVALID_CREDENTIALS','Email atau password tidak dapat digunakan. Periksa akun dan verifikasi email Anda.');
   s.accountEmail=email;s.accountName=account.name;s.role='reporter';s.page='RP01';s.accountMessage=null;
   notice(s,'Login contoh selesai. Tidak ada autentikasi ke layanan nyata.');
  }else if(purpose==='AK02'||purpose==='AK05'){
   ensure(email.includes('@'),'INVALID_PAYLOAD','Isi email contoh yang valid.');
   if(purpose==='AK02'){
    ensure(p.name?.trim(),'INVALID_PAYLOAD','Nama lengkap wajib diisi.');
    if(!s.demoAccounts[email])s.demoAccounts[email]={password:p.password,name:p.name.trim(),verified:false};
   }
   s.accountMessage='Jika alamat memenuhi syarat, petunjuk dan kode akan dikirim melalui email. Periksa email terbaru Anda.';
   s.accountPurpose=purpose==='AK05'?'PASSWORD_RESET':'EMAIL_VERIFICATION';
   s.demoChallenge={email,purpose:s.accountPurpose};
  }else{
   if(purpose==='AK03'){
    const challenge=s.demoChallenge;
    ensure(!challenge||challenge.purpose==='EMAIL_VERIFICATION','OTP_INVALID','Kode tidak dapat digunakan untuk tindakan ini. Gunakan email sesuai tujuan.');
    if(challenge&&s.demoAccounts[challenge.email]){s.demoAccounts[challenge.email].verified=true;s.accountEmail=challenge.email;}
    s.demoChallenge=null;
   }
   if(purpose==='AK06'){
    const challenge=s.demoChallenge;
    ensure(!challenge||challenge.purpose==='PASSWORD_RESET','OTP_INVALID','Kode tidak dapat digunakan untuk tindakan ini. Gunakan email sesuai tujuan.');
    const targetEmail=challenge?.email||s.accountEmail,account=s.demoAccounts[targetEmail];
    ensure(account,'OTP_INVALID','Kode tidak dapat digunakan. Periksa kembali email terbaru.');
    account.password=p.password;s.accountEmail=targetEmail;s.demoChallenge=null;
   }
   if(purpose==='AK04'){const target=s.operators.find(o=>!o.verified);if(target){target.verified=true;target.active=true;}}
   s.page='AK01';s.accountMessage=null;notice(s,'Tindakan akun contoh berhasil. Silakan masuk.');
  }return;
 }
 if(action==='CREATE_OPERATOR'){online(s);ensure(s.role==='admin','PERMISSION_DENIED','Pengelolaan akun memerlukan Admin.');ensure(p.name?.trim()&&p.email?.includes('@'),'INVALID_PAYLOAD','Nama dan email wajib diisi.');ensure((p.permissions||[]).every(x=>operatorPermissions.includes(x)),'INVALID_PAYLOAD','Izin tidak termasuk katalog Operator.');s.operators.push({id:uid(s.nextId++),name:p.name.trim(),email:p.email,active:false,verified:false,permissions:p.permissions||[]});notice(s,'Akun contoh dibuat belum aktif. Pemilik menetapkan password melalui aktivasi email.');return;}
 if(action==='PATCH_OPERATOR'){online(s);ensure(s.role==='admin','PERMISSION_DENIED','Pengelolaan akun memerlukan Admin.');const o=s.operators.find(o=>o.id===p.id);ensure(o,'NOT_FOUND','Akun tidak tersedia.');ensure(p.name?.trim(),'INVALID_PAYLOAD','Nama wajib diisi.');ensure(!p.active||o.verified,'ACTIVATION_NOT_ALLOWED','Akun belum diaktivasi. Admin tidak dapat melewati aktivasi pemilik.');ensure((p.permissions||[]).every(x=>operatorPermissions.includes(x)),'INVALID_PAYLOAD','Izin tidak termasuk katalog Operator.');Object.assign(o,{name:p.name.trim(),active:!!p.active,permissions:p.permissions||[]});notice(s,'Perubahan akun contoh tersimpan; izin saat ini berlaku pada akses berikutnya.');return;}
 if(action==='RESEND_ACTIVATION'){online(s);ensure(s.role==='admin','PERMISSION_DENIED','Pengiriman ulang aktivasi memerlukan Admin.');const o=s.operators.find(o=>o.id===p.id);ensure(o&&!o.verified,'ACTIVATION_NOT_ALLOWED','Akun sudah menyelesaikan aktivasi.');if(s.scenario==='OTP_INVALID')problem('OTP_DELIVERY_FAILED','Pengiriman aktivasi gagal pada skenario contoh. Akun tetap belum aktif.');notice(s,'Pengiriman ulang aktivasi contoh tercatat. Kode hanya diterima pemilik melalui email.');return;}
 if(action==='PROFILE'){online(s);ensure(p.name.trim(),'INVALID_PAYLOAD','Nama wajib diisi.');s.accountName=p.name.trim();if(s.demoAccounts[s.accountEmail])s.demoAccounts[s.accountEmail].name=s.accountName;notice(s,'Nama profil contoh diperbarui.');return;}
 if(action==='MARK_READ'){online(s);s.notificationRead.push(p.id);return;}
 problem('UNKNOWN_ACTION','Tindakan tidak dikenali.');
}
