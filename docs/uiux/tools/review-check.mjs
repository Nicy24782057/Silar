import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath,pathToFileURL} from 'node:url';

// Pemeriksaan logika dan proyeksi HTML; tidak mengukur tata letak browser.
const rootPath=fileURLToPath(new URL('..',import.meta.url));
const assetPath=fs.existsSync(path.join(rootPath,'dist','model.mjs'))?path.join(rootPath,'dist'):path.join(rootPath,'prototype');
const model=await import(pathToFileURL(path.join(assetPath,'model.mjs')).href);
const {initial,current,act,uid,demoLogin,operatorPermissions,readable,fullReadable}=model;
const source=fs.readFileSync(path.join(assetPath,'app.mjs'),'utf8');
const root={innerHTML:''},listeners={};
const context={...model,console,setTimeout:()=>0,setInterval:()=>0,clearInterval:()=>{},requestAnimationFrame:()=>{},URL:{},document:{querySelector:q=>q==='#app'?root:null,querySelectorAll:()=>[],addEventListener:(type,fn)=>listeners[type]=fn}};
vm.createContext(context);
vm.runInContext(source.replace(/^import .*?;\r?\n/,'')+'\nglobalThis.reviewHarness={state:v=>{s=v;modal=null;publicFilter={q:"",category:"",location:""};},filter:v=>publicFilter=v,render};',context);
const h=context.reviewHarness;
const render=(s,page=s.page)=>{s.page=page;h.state(s);h.render();return root.innerHTML;};
const click=(action,data={})=>listeners.click({target:{closest:()=>({dataset:{action,...data}})}});
const articles=()=>root.innerHTML.match(/<article\b[^>]*>[\s\S]*?<\/article>/g)||[];
const rejects=(fn,code)=>assert.throws(fn,e=>e.code===code);
function assigned(){const s=initial();s.role='operator';s.selectedId=uid(2);act(s,'CLAIM');return s;}
function reviewed(){const s=assigned();act(s,'REVIEW',{outcome:'VALID',reason:'Pemeriksaan contoh.'});return s;}
const publicData={summary:'Ringkasan publik terbaru.',general_location:'Kawasan Mawar',time_text:'Sore',general_impact:'Jalan terdampak',handling_update:'Petugas mencatat penanganan'};
function candidate(s,data=publicData){act(s,'DECISION',{decision:'PREPARE',reason:'Informasi umum.'});act(s,'CREATE_CANDIDATE',{data});}
function publish(s){s.publicationChecked=true;act(s,'APPROVE');act(s,'PUBLISH');}
const results=[];
function check(id,scenario,name,expected,fn){
 try{const observed=fn();results.push({id,scenario,name,expected,observed,status:'LULUS_TEKNIS'});console.log('PASS '+id+' '+name);}
 catch(e){results.push({id,scenario,name,expected,observed:e.message,status:'GAGAL_TEKNIS'});console.log('FAIL '+id+' '+name+' — '+e.message);}
}

check('RT-01','U07-01','Uji ulang password salah dan OTP kedaluwarsa','Akun tetap di halaman masuk; kode kedaluwarsa tidak mengaktifkan akun.',()=>{
 const s=initial();s.role='account';s.page='AK01';rejects(()=>act(s,'AUTH',{email:demoLogin.email,password:'Salah123!'}),'INVALID_CREDENTIALS');assert.equal(s.page,'AK01');assert.equal(s.role,'account');
 s.page='AK02';act(s,'AUTH',{email:'uji-ulang@contoh.test',name:'Uji Ulang',password:'Contoh123!',password_confirm:'Contoh123!'});s.page='AK03';s.scenario='OTP_EXPIRED';rejects(()=>act(s,'AUTH',{code:'123456'}),'OTP_EXPIRED');assert.equal(s.demoAccounts['uji-ulang@contoh.test'].verified,false);
 return 'Password salah ditolak dengan INVALID_CREDENTIALS; OTP_EXPIRED tidak mengubah verified=false.';
});
check('RT-02','U07-11','Pemisahan persiapan, kandidat, approval, publish','Portal hanya mendapat versi setelah tindakan Terbitkan; checklist wajib.',()=>{
 const s=reviewed(),r=current(s);act(s,'DECISION',{decision:'PREPARE',reason:'Informasi umum.'});assert.equal(r.candidate,null);assert.equal(r.publicVersion,null);act(s,'CREATE_CANDIDATE',{data:publicData});assert.equal(r.publicVersion,null);rejects(()=>act(s,'APPROVE'),'INVALID_PAYLOAD');const v=r.candidate.version;s.publicationChecked=true;act(s,'APPROVE');assert.equal(r.publicVersion,null);act(s,'PUBLISH');assert.equal(r.publicVersion.version,v);assert.notEqual(r.workflow,'CLOSED');
 return 'Tidak terbit pada PREPARE/DRAFT/APPROVED; versi yang disetujui terbit dan penanganan tetap terbuka.';
});
check('RT-03','U07-11','Sanitasi dan pembatalan kandidat pengganti','Field privat ditolak; pembatalan DRAFT maupun APPROVED mempertahankan versi terbit.',()=>{
 const s=reviewed();act(s,'DECISION',{decision:'PREPARE',reason:'Informasi umum.'});rejects(()=>act(s,'CREATE_CANDIDATE',{data:{...publicData,email:'privat@contoh.test'}}),'INVALID_PAYLOAD');act(s,'CREATE_CANDIDATE',{data:publicData});publish(s);const r=current(s),old=structuredClone(r.publicVersion);
 for(const approve of [false,true]){candidate(s,{...publicData,summary:'Pengganti belum terbit'});if(approve){s.publicationChecked=true;act(s,'APPROVE');}rejects(()=>act(s,'CANCEL_CANDIDATE',{reason:''}),'INVALID_PAYLOAD');act(s,'CANCEL_CANDIDATE',{reason:'Perlu pemeriksaan ulang.'});assert.deepEqual(r.publicVersion,old);assert.equal(r.candidate,null);}
 rejects(()=>act(s,'REVIEW',{outcome:'INVALID',reason:'Uji ulang'}),'TRANSITION_REJECTED');
 return 'Allowlist menolak email; dua pembatalan tidak mengganti versi publik; review ulang setelah terbit ditolak.';
});
check('RT-04','U07-12','Prasyarat penutupan','Close ditahan tanpa review, keputusan final, tindak lanjut selesai, atau saat kandidat aktif.',()=>{
 let s=assigned();rejects(()=>act(s,'CLOSE',{note:'Tutup'}),'TRANSITION_REJECTED');s=reviewed();rejects(()=>act(s,'CLOSE',{note:'Tutup'}),'TRANSITION_REJECTED');act(s,'DECISION',{decision:'INTERNAL',reason:'Internal'});act(s,'FOLLOWUP',{description:'Tindakan contoh'});rejects(()=>act(s,'CLOSE',{note:'Tutup'}),'TRANSITION_REJECTED');act(s,'FINISH_FOLLOWUP',{id:current(s).followups[0].id,status:'DONE'});candidate(s);rejects(()=>act(s,'CLOSE',{note:'Tutup'}),'TRANSITION_REJECTED');
 return 'Empat keadaan yang belum memenuhi syarat seluruhnya menghasilkan TRANSITION_REJECTED.';
});
check('RT-05','U07-12','Jalur internal/terbit dan CLOSED terminal','Kedua jalur sah dapat ditutup; mutasi berikutnya ditolak dan riwayat tetap terbaca.',()=>{
 for(const route of ['INTERNAL','PUBLISHED']){const s=reviewed(),r=current(s);if(route==='INTERNAL')act(s,'DECISION',{decision:'INTERNAL',reason:'Internal'});else{candidate(s);publish(s);}rejects(()=>act(s,'CLOSE',{note:''}),'INVALID_PAYLOAD');act(s,'CLOSE',{note:'Pemeriksaan selesai'});assert.equal(r.workflow,'CLOSED');for(const [action,payload] of [['REVIEW',{outcome:'VALID',reason:'Ulang'}],['FOLLOWUP',{description:'Baru'}],['DECISION',{decision:'PREPARE',reason:'Baru'}]])rejects(()=>act(s,action,payload),'PERMISSION_DENIED');assert.ok(readable(s,r));assert.ok(r.history.length>0);s.role='admin';rejects(()=>act(s,'ASSIGN',{operator:'op-b',reason:'Alih'}),'PERMISSION_DENIED');}
 return 'INTERNAL/PUBLISHED ditutup dengan catatan; review, tindak lanjut, publikasi dan assignment setelah CLOSED ditolak.';
});
check('RT-06','U07-13','Akun dan aktivasi Operator','Akun awal belum aktif; Admin tidak dapat melewati aktivasi pemilik.',()=>{
 const s=initial();s.role='admin';act(s,'CREATE_OPERATOR',{name:'Petugas Uji',email:'petugas-uji@contoh.test',permissions:operatorPermissions});const o=s.operators.at(-1);assert.equal(o.active,false);assert.equal(o.verified,false);assert.equal('password' in o,false);rejects(()=>act(s,'PATCH_OPERATOR',{id:o.id,name:o.name,active:true,permissions:o.permissions}),'ACTIVATION_NOT_ALLOWED');act(s,'RESEND_ACTIVATION',{id:o.id});s.role='account';rejects(()=>act(s,'RESEND_ACTIVATION',{id:o.id}),'PERMISSION_DENIED');s.page='AK04';act(s,'AUTH',{code:'123456',password:'Contoh123!',password_confirm:'Contoh123!'});assert.equal(s.operators.find(o=>o.id==='op-new').active,true);
 return 'Akun baru belum aktif/tanpa password Admin; resend hanya Admin; aktivasi fixture mengaktifkan akun contoh pertama yang belum diverifikasi.';
});
check('RT-07','U07-13','Pengalihan dan pencabutan izin','Alasan wajib; akses lama dicabut; penonaktifan/izin berlaku pada tindakan berikutnya.',()=>{
 const s=assigned(),r=current(s);s.role='admin';rejects(()=>act(s,'ASSIGN',{operator:'op-b',reason:''}),'INVALID_PAYLOAD');act(s,'ASSIGN',{operator:'op-b',reason:'Pengalihan tugas'});s.role='operator';assert.equal(readable(s,r),false);s.operator='op-b';assert.equal(readable(s,r),true);s.role='admin';act(s,'PATCH_OPERATOR',{id:'op-b',name:'Operator B',active:true,permissions:['view_assigned_report']});s.role='operator';rejects(()=>act(s,'REVIEW',{outcome:'VALID',reason:'Uji'}),'PERMISSION_DENIED');s.role='admin';act(s,'PATCH_OPERATOR',{id:'op-b',name:'Operator B',active:false,permissions:operatorPermissions});s.role='operator';assert.equal(readable(s,r),false);
 return 'Assignment tanpa alasan ditolak; B memperoleh akses, A kehilangan akses; izin dicabut/nonaktif menahan tindakan berikutnya.';
});
check('RT-08','U07-13','Proyeksi Admin, audit dan monitoring','Draft/isi privat tidak terbuka otomatis; audit tidak merender narasi; monitoring hanya metadata.',()=>{
 const s=reviewed(),r=current(s);r.card.narrative='RAHASIA_NARASI_RT08';r.review.reason='RAHASIA_REVIEW_RT08';s.role='admin';assert.equal(readable(s,s.reports[0]),false);assert.equal(fullReadable(s,r),false);s.adminPrivate=true;assert.equal(fullReadable(s,r),true);let html=render(s,'AD03');assert.ok(!html.includes('RAHASIA_NARASI_RT08'));assert.ok(!html.includes('RAHASIA_REVIEW_RT08'));s.scenario='CONFIG_NOT_READY';html=render(s,'AD04');assert.ok(html.includes('NOT_CONFIGURED'));assert.ok(!html.includes('data-action="analyse"'));rejects(()=>act(s,'REVIEW',{outcome:'VALID',reason:'Admin'}),'PERMISSION_DENIED');
 return 'Draft dan bukti privat dibatasi; audit merender metadata tindakan; NOT_CONFIGURED tersedia tanpa tombol menjalankan model.';
});
check('RT-09','U07-14','Pencarian, kategori dan lokasi umum','Pencarian empat field publik tidak peka kapital; kombinasi filter bekerja dan hasil kosong dijelaskan.',()=>{
 const s=reviewed();candidate(s);publish(s);s.role='public';render(s,'PB01');assert.equal(articles().length,2);
 for(const q of ['TERBARU','MAWAR','JALAN TERDAMPAK','PETUGAS']){h.filter({q,category:'FLOOD',location:'MAWAR'});h.render();assert.equal(articles().length,1);assert.ok(articles()[0].includes('Ringkasan publik terbaru.'));}
 h.filter({q:'',category:'FIRE',location:'Mawar'});h.render();assert.equal(articles().length,0);assert.ok(root.innerHTML.includes('Tidak ada informasi yang sesuai'));
 return 'Empat field pencarian cocok tanpa peka kapital; filter gabungan sesuai; kategori yang berbeda menampilkan pesan kosong.';
});
check('RT-10','U07-14','Urutan publikasi terbaru','Publikasi baru muncul sebelum versi fixture yang terbit lebih awal.',()=>{
 const s=reviewed();candidate(s);publish(s);s.role='public';render(s,'PB01');assert.ok(articles()[0].includes('Ringkasan publik terbaru.'),'Informasi lama muncul lebih dahulu daripada publikasi baru.');
 return 'Artikel pertama adalah publikasi yang baru dibuat dalam sesi, disusul publikasi fixture lama.';
});
check('RT-11','U07-14','Batas informasi publik','Detail memuat versi publik, waktu kejadian dan publikasi; narasi privat/catatan internal tidak muncul.',()=>{
 const s=reviewed(),r=current(s);r.card.narrative='RAHASIA_NARASI_RT11';r.card.location='RAHASIA_ALAMAT_RT11';r.review.reason='RAHASIA_REVIEW_RT11';candidate(s);publish(s);s.role='public';let html=render(s,'PB01');assert.ok(html.includes('Kejadian: Sore'));assert.ok(html.includes('Terbit:'));html=render(s,'PB02');for(const secret of ['RAHASIA_NARASI_RT11','RAHASIA_ALAMAT_RT11','RAHASIA_REVIEW_RT11'])assert.ok(!html.includes(secret));assert.ok(html.includes('Ringkasan publik terbaru.'));s.selectedId=uid(1);html=render(s,'PB02');assert.ok(html.includes('Akses dibatasi'));
 return 'Daftar membedakan dua waktu; detail hanya data publik; laporan tanpa versi terbit ditolak.';
});
check('RT-12','U07-15','Notifikasi baca, tujuan dan akses lama','Penerima dibatasi; tandai dibaca bekerja; notifikasi lama tidak memulihkan akses setelah assignment berubah.',()=>{
 const s=initial();s.role='admin';s.selectedId=uid(3);act(s,'ASSIGN',{operator:'op-b',reason:'Pengalihan'});s.role='operator';s.operator='op-a';let html=render(s,'UM01');assert.ok(html.includes('data-id="2"'));click('mark-read',{id:'2'});assert.ok(s.notificationRead.includes(2));assert.ok(root.innerHTML.includes('Sudah dibaca'));click('open-notification',{id:'2'});assert.equal(s.page,'OP03');assert.ok(root.innerHTML.includes('Akses dibatasi'));s.operator='op-b';html=render(s,'UM01');assert.ok(!html.includes('data-action="open-notification" data-id="2"'));assert.ok(html.includes('Anda menerima penugasan laporan.'));
 return 'Notifikasi A dapat ditandai dibaca; tautan lama ditolak setelah pengalihan; notifikasi penugasan baru tersedia bagi B.';
});
check('RT-13','U07-15','Pemicu notifikasi laporan','Submit, review, assignment, publikasi dan close menghasilkan pemberitahuan dalam aplikasi.',()=>{
 const submitted=initial();act(submitted,'SAMPLE');act(submitted,'SAVE');act(submitted,'ANALYSE');act(submitted,'FINISH');act(submitted,'CONFIRM');act(submitted,'SUBMIT');assert.ok(submitted.notifications.some(n=>n.kind==='SUBMITTED'&&n.reportId===uid(1)));submitted.role='admin';act(submitted,'ASSIGN',{operator:'op-b',reason:'Penugasan baru'});assert.ok(submitted.notifications.some(n=>n.kind==='ASSIGNED'&&n.operator==='op-b'&&n.reportId===uid(1)));
 const s=reviewed();assert.ok(s.notifications.some(n=>n.kind==='REVIEWED'&&n.role==='reporter'));candidate(s);publish(s);act(s,'CLOSE',{note:'Selesai'});for(const kind of ['REVIEWED','PUBLISHED','CLOSED'])assert.ok(s.notifications.some(n=>n.kind===kind&&n.role==='reporter'));s.role='reporter';let html=render(s,'UM01');assert.ok(html.includes('PUBLISHED'));assert.ok(html.includes('CLOSED'));assert.ok(!html.includes('Anda menerima penugasan laporan.'));
 return 'Notifikasi sesuai peran dan jenis kejadian tersedia di aplikasi; tidak menggunakan layanan kirim pesan eksternal.';
});
check('RT-14','U07-15','Offline dan panduan instalasi','Operasi laporan ditahan saat offline; panduan tidak menjanjikan sinkronisasi draft offline.',()=>{
 const s=initial();act(s,'SCENARIO',{value:'OFFLINE'});rejects(()=>act(s,'SAVE'),'OFFLINE');let html=render(s,'RP02');assert.ok(!html.includes('id="image-file"'));assert.ok(html.includes('koneksi'));act(s,'SCENARIO',{value:'NORMAL'});html=render(s,'UM02');assert.ok(html.includes('Tidak ada sinkronisasi draft offline'));assert.ok(!/localStorage|sessionStorage|indexedDB|fetch\s*\(|XMLHttpRequest/.test(source));
 return 'SAVE ditolak OFFLINE, formulir operasi tidak dirender; panduan menjelaskan kebutuhan koneksi tanpa cache data privat.';
});
check('RT-15','U07-16','Keberadaan pesan Digital Awareness','Panduan/layar relevan memuat informasi AI, Gemini, OTP, kategori, sanitasi dan batas pemulihan.',()=>{
 const s=initial();const compose=render(s,'RP02');for(const phrase of ['kebakaran, banjir, gempa bumi, dan kecelakaan','menjadi hak Anda','informasi pribadi','Gemini','Audio asli tetap diproses lokal'])assert.ok(compose.includes(phrase),phrase);s.role='account';const auth=render(s,'AK03');assert.ok(auth.includes('Jaga kerahasiaan password dan OTP'));const guide=render(s,'GUIDE');assert.ok(guide.includes('Alur pemulihan'));const reviewedState=reviewed();candidate(reviewedState);const publication=render(reviewedState,'OP05');assert.ok(publication.includes('sanitasi'));assert.ok(publication.includes('mengidentifikasi pihak'));
 return 'Informasi ditemukan pada sumber/proyeksi HTML. Keterbacaan, pemahaman pengguna, fokus dan layout belum dinilai oleh pemeriksaan ini.';
});

const report={title:'Bukti Pemeriksaan Teknis SLR_07',executed_at:new Date().toISOString(),method:'Node.js: perilaku model, handler klik, dan proyeksi HTML pada stub DOM; bukan browser.',node_version:process.version,scope:'Prototype dengan data fiktif; tanpa API/AI/email/PWA nyata.',browser_visual_qa:false,manual_tester:'Tidak diatribusikan kepada penguji manual.',asset_sha256:{},summary:{passed:results.filter(r=>r.status==='LULUS_TEKNIS').length,failed:results.filter(r=>r.status==='GAGAL_TEKNIS').length,total:results.length},results,manual_follow_up:['Uji visual ulang menu/avatar pada paket hasil perbaikan audit.','U07-16: perangkat/browser sasaran, keyboard, fokus dan review usability kelompok.','Penerimaan akhir kelompok dan commit repository SILAR yang sebenarnya.']};
const {createHash}=await import('node:crypto');
for(const name of ['index.html','styles.css','app.mjs','model.mjs'])report.asset_sha256[name]=createHash('sha256').update(fs.readFileSync(path.join(assetPath,name))).digest('hex');
const reportIndex=process.argv.indexOf('--report');
if(reportIndex>=0){const destination=process.argv[reportIndex+1];assert.ok(destination,'Jalur --report wajib diisi.');fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,JSON.stringify(report,null,2)+'\n');}
console.log(`\n${report.summary.passed}/${results.length} pemeriksaan teknis lulus; browser/visual QA tidak dilakukan.`);
if(report.summary.failed)process.exitCode=1;
