export const hasPermission = (user, permission) => Boolean(user && user.effective_permissions?.includes(permission));
export const isStaff = user => ['OPERATOR', 'ADMIN'].includes(user?.role);
export const roleLabel = role => ({REPORTER:'Reporter', OPERATOR:'Operator', ADMIN:'Admin'}[role] || 'Akun');
export const shortId = value => value ? '#' + String(value).slice(0, 8) : 'Belum tersedia';
export const initials = name => String(name || '').trim().split(/\s+/).slice(0, 2).map(x => x[0] || '').join('').toUpperCase();
export const personName = (person, fallback='Belum ditugaskan') => person?.full_name?.trim() || person?.operator_name?.trim() || person?.actor_name?.trim() || fallback;
export const permissionLabels = {
  view_queue:'Melihat antrean laporan resmi', view_assigned_report:'Membaca laporan yang ditugaskan',
  claim_report:'Mengklaim laporan', review_report:'Mencatat review dan validasi',
  manage_followup:'Mengelola tindak lanjut', publish_report:'Menentukan arah publikasi', close_report:'Menutup laporan',
  manage_operator:'Mengelola akun Operator', assign_report:'Menugaskan dan mengalihkan laporan',
  monitor_report:'Memantau laporan resmi', view_audit:'Membaca audit aktivitas', monitor_services:'Memantau layanan'
};
export const workflowOptions = [
  {value:'SUBMITTED',label:'Belum ditugaskan'}, {value:'ASSIGNED',label:'Ditugaskan'},
  {value:'IN_REVIEW',label:'Dalam review'}, {value:'FOLLOW_UP',label:'Tindak lanjut'}, {value:'CLOSED',label:'Ditutup'}
];
export const categoryOptions = [
  {value:'FLOOD',label:'Banjir'}, {value:'EARTHQUAKE',label:'Gempa bumi'}, {value:'FIRE',label:'Kebakaran'}, {value:'ACCIDENT',label:'Kecelakaan'}
];
export const workspaceLabel = value => ({PENDING:'Menunggu',DONE:'Selesai',CANCELLED:'Dibatalkan',PREPARE:'Siapkan publikasi',
  PENDING_APPROVAL:'Persiapan publikasi',NOT_DECIDED:'Belum diputuskan',INTERNAL:'Internal',PUBLISHED:'Terbit',
  APPROVED:'Disetujui',VALID:'Valid',INVALID:'Tidak valid',INCONCLUSIVE:'Belum dapat dipastikan',
  NOT_REVIEWED:'Belum direview',ASSIGNED:'Ditugaskan',SUBMITTED:'Belum ditugaskan',IN_REVIEW:'Dalam review',
  FOLLOW_UP:'Tindak lanjut',CLOSED:'Ditutup',SELF_CLAIM:'Klaim mandiri',ADMIN_ASSIGNMENT:'Penugasan Admin',
  ADMIN_REASSIGNMENT:'Pengalihan Admin'}[value] || value || 'Belum tersedia');
export const statusTone = value => ['NOT_REVIEWED','NOT_DECIDED'].includes(value) ? 'grey' :
  ['CLOSED','VALID','DONE','PUBLISHED'].includes(value) ? 'success' :
  ['INVALID','CANCELLED','FAILED'].includes(value) ? 'danger' :
  ['PENDING','SUBMITTED','INCONCLUSIVE','PENDING_APPROVAL'].includes(value) ? 'warning' :
  ['FOLLOW_UP','IN_REVIEW'].includes(value) ? 'purple' : 'blue';
export const eventLabels = {
  OPERATOR_CREATED:'Akun Operator dibuat',OPERATOR_UPDATED:'Akun Operator diperbarui',OTP_DISPATCH_PREPARED:'Petunjuk akun disiapkan',
  OTP_DELIVERY_FAILED:'Pengiriman petunjuk gagal',REPORT_SUBMITTED:'Laporan resmi dikirim',REPORT_ASSIGNED:'Laporan ditugaskan',
  REPORT_CLAIMED:'Laporan diklaim',REPORT_REASSIGNED:'Penanggung jawab dialihkan',REVIEW_RECORDED:'Review dicatat',
  FOLLOW_UP_UPDATED:'Tindak lanjut diperbarui',PUBLICATION_DIRECTION_RECORDED:'Arah publikasi dicatat',REPORT_CLOSED:'Laporan ditutup',
  ACCOUNT_ACCOUNT_ACTIVATION:'Akun Operator diaktifkan',ACCOUNT_PROFILE_UPDATED:'Profil diperbarui',ACCOUNT_LOGIN:'Akun masuk'
};
export function workspaceNavigation(user) {
  const rows = [{label:'Dashboard',to:'/workspace',icon:'dashboard'}];
  const add=(permission,label,to,icon,admin=false)=>{
    if(hasPermission(user,permission)&&(!admin||user.role==='ADMIN'))rows.push({permission,label,to,icon});
  };
  add('monitor_report','Monitoring Laporan','/workspace/monitoring','chart',true);
  add('assign_report','Penugasan','/workspace/assignments','clipboard',true);
  add('manage_operator','Manajemen Operator','/workspace/operators','users',true);
  add('view_queue','Antrean Laporan','/workspace/queue','reports');
  add('view_assigned_report','Penanganan Saya','/workspace/assigned','clipboard');
  add('view_audit','Audit Aktivitas','/workspace/audit','history');
  add('monitor_services','Monitoring Layanan','/workspace/services','server');
  rows.push({label:'Notifikasi',to:'/notifications',icon:'bell'});
  return rows;
}
export function workspaceReportsPath(scope,filters={}) {
  if(!['queue','assigned','monitor','assignment'].includes(scope))throw new Error('Scope tidak sah.');
  const params=new URLSearchParams({scope,page_size:'10',ordering:filters.ordering||'-submitted_at'});
  for(const key of ['q','event_type','workflow_status','validation_status','followup_status','active','unassigned','page'])if(filters[key])params.set(key,filters[key]);
  return 'workspace/reports/?'+params;
}
export function handlerCan(user, detail, permission) {
  return Boolean(isStaff(user)&&detail?.private_access&&detail?.assignment?.operator_id===user.id&&
    detail?.report?.workflow_status!=='CLOSED'&&hasPermission(user,'view_assigned_report')&&hasPermission(user,permission));
}
export function closeAllowed(user,detail) {
  return handlerCan(user,detail,'close_report')&&detail.close_requirements?.every(item=>item.met)===true;
}
export function decisionAllowed(detail,decision) {
  return Boolean(detail?.reviews?.length&&!detail.has_active_candidate&&
    !['APPROVED','PUBLISHED'].includes(detail.report.publication_status)&&
    (decision==='INTERNAL'||decision==='PREPARE'&&detail.report.validation_status==='VALID'));
}
export function assignmentTargetAvailable(target,currentId=null) {
  return Boolean(target?.id&&target.id!==currentId);
}
const operatorViews=Object.freeze({
  active:{title:'Dalam penanganan',caption:'Laporan aktif yang menjadi tanggung jawab Anda.',filters:{active:'true'}},
  review:{title:'Perlu direview',caption:'Laporan aktif Anda yang belum memiliki review resmi.',filters:{active:'true',validation_status:'NOT_REVIEWED'}},
  followup:{title:'Tindak lanjut pending',caption:'Laporan aktif Anda yang masih memiliki tindak lanjut menunggu.',filters:{active:'true',followup_status:'PENDING'}}
});
const adminViews=Object.freeze({
  official:{title:'Laporan resmi',caption:'Seluruh laporan resmi yang sudah dikirim, termasuk laporan dalam penanganan dan yang telah ditutup.',filters:{}},
  unassigned:{title:'Belum ditugaskan',caption:'Laporan resmi aktif yang belum memiliki penanggung jawab saat ini.',filters:{active:'true',unassigned:'true'}},
  closed:{title:'Laporan ditutup',caption:'Laporan resmi yang penanganannya sudah ditutup.',filters:{workflow_status:'CLOSED'}}
});
export function workspaceQuickView(scope,view){
  const views=scope==='assigned'?operatorViews:['monitor','assignment'].includes(scope)?adminViews:null;
  return views&&typeof view==='string'&&Object.hasOwn(views,view)?views[view]:null;
}
export function workspaceEffectiveFilters(filters,view){
  return {...filters,...(view?.filters||{})};
}
export function dashboardCardLink(user,key){
  if(!isStaff(user))return null;
  if(user.role==='ADMIN'){
    const reports=hasPermission(user,'monitor_report')?'/workspace/monitoring':hasPermission(user,'assign_report')?'/workspace/assignments':null;
    if(key==='official')return reports?reports+'?view=official':null;
    if(key==='closed')return reports?reports+'?view=closed':null;
    if(key==='unassigned'){
      const target=hasPermission(user,'assign_report')?'/workspace/assignments':reports;
      return target?target+'?view=unassigned':null;
    }
    if(key==='operators')return hasPermission(user,'manage_operator')?'/workspace/operators?status=active':null;
  }
  if(key==='queue')return hasPermission(user,'view_queue')?'/workspace/queue':null;
  const views={assigned:'active',review_pending:'review',followup_pending:'followup'};
  return Object.hasOwn(views,key)&&hasPermission(user,'view_assigned_report')?'/workspace/assigned?view='+views[key]:null;
}
export function operatorStatusFilter(value){
  return typeof value==='string'&&['active','pending','inactive'].includes(value)?value:'';
}
export function reportTabLocked(detail,key){
  if(!['followup','decision'].includes(key))return false;
  const report=detail?.report,cardId=report?.official_card_version_id;
  return !Boolean(cardId&&['VALID','INVALID','INCONCLUSIVE'].includes(report.validation_status)&&detail?.reviews?.some(review=>review.card_version_id===cardId));
}
