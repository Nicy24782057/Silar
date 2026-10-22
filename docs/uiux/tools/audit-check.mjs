import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const rootPath=fileURLToPath(new URL('..',import.meta.url));
const assetPath=fs.existsSync(path.join(rootPath,'dist','model.mjs'))?path.join(rootPath,'dist'):path.join(rootPath,'prototype');
const model=await import(pathToFileURL(path.join(assetPath,'model.mjs')).href);
const app=fs.readFileSync(path.join(assetPath,'app.mjs'),'utf8');
const css=fs.readFileSync(path.join(assetPath,'styles.css'),'utf8');
function harness(){
 const root={innerHTML:''},listeners={};
 const context={...model,console,setTimeout:()=>0,setInterval:()=>0,clearInterval:()=>{},requestAnimationFrame:()=>{},URL:{},document:{querySelector:q=>q==='#app'?root:null,querySelectorAll:()=>[],addEventListener:(type,fn)=>listeners[type]=fn}};
 vm.createContext(context);
 vm.runInContext(app.replace(/^import .*?;\r?\n/,'')+'\nglobalThis.auditHarness={state:v=>{s=v;modal=null;menuOpen=false;},getState:()=>s,getMenu:()=>menuOpen,render};',context);
 const h=context.auditHarness;
 return {root,h,click:(action,data={})=>listeners.click({target:{closest:()=>({dataset:{action,...data}})}})};
}
function rgb(hex){assert.match(hex,/^#[0-9a-f]{6}$/i);return [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255);}
function luminance(hex){const [r,g,b]=rgb(hex).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*r+.7152*g+.0722*b;}
function contrast(a,b){const la=luminance(a),lb=luminance(b);return (Math.max(la,lb)+.05)/(Math.min(la,lb)+.05);}
const results=[];
function check(id,issue,name,fn){try{const observed=fn();results.push({id,issue,name,status:'LULUS_TEKNIS',observed});console.log('PASS '+id+' '+name);}catch(e){results.push({id,issue,name,status:'GAGAL_TEKNIS',observed:e.message});console.log('FAIL '+id+' '+name+' — '+e.message);}}
check('AR07-01','A07-01','Menu ditutup ketika membuka draft yang sudah ada',()=>{
 const {root,h,click}=harness(),s=model.initial();h.state(s);h.render();const before=s.reports.length,draft=model.current(s).id;
 click('menu');assert.equal(h.getMenu(),true);assert.ok(root.innerHTML.includes('app-frame menu-open'));
 click('new-report');assert.equal(s.page,'RP02');assert.equal(s.selectedId,draft);assert.equal(s.reports.length,before);assert.equal(h.getMenu(),false,'Menu masih terbuka setelah membuka draft.');assert.ok(!root.innerHTML.includes('app-frame menu-open'));assert.ok(root.innerHTML.includes('id="report-text"'));
 return 'RP02 membuka draft yang sama tanpa duplikasi; class menu-open hilang dan formulir dirender.';
});
check('AR07-02','A07-01','Menu ditutup ketika membuat draft baru dan tidak menduplikasi draft',()=>{
 const {root,h,click}=harness(),s=model.initial();s.reports[0].workflow='SUBMITTED';h.state(s);h.render();const before=s.reports.length;
 click('menu');click('new-report');assert.equal(s.page,'RP02');assert.equal(s.reports.length,before+1);assert.equal(model.current(s).workflow,'NOT_SUBMITTED');assert.equal(h.getMenu(),false,'Menu masih terbuka setelah membuat draft baru.');assert.ok(!root.innerHTML.includes('app-frame menu-open'));const newId=s.selectedId;
 click('menu');click('new-report');assert.equal(s.selectedId,newId);assert.equal(s.reports.length,before+1);assert.equal(h.getMenu(),false);assert.ok(root.innerHTML.includes('id="report-text"'));
 return 'Satu draft baru dibuat; menu tertutup pada kedua navigasi; membuka ulang memakai draft tersebut.';
});
check('AR07-03','A07-02','Kontras warna teks avatar minimal 4,5:1',()=>{
 const rule=css.match(/\.user-avatar\s*\{([^}]+)\}/)?.[1];assert.ok(rule,'Aturan avatar tidak ditemukan.');
 const bg=rule.match(/(?:^|;)\s*background\s*:\s*(#[0-9a-f]{6})/i)?.[1];
 const declared=rule.match(/(?:^|;)\s*color\s*:\s*([^;]+)/)?.[1]?.trim();
 const muted=css.match(/--muted\s*:\s*(#[0-9a-f]{6})/i)?.[1];
 const ink=css.match(/--ink\s*:\s*(#[0-9a-f]{6})/i)?.[1];
 const fg=declared==='var(--ink)'?ink:declared==='var(--muted)'?muted:declared||muted;
 const ratio=contrast(fg,bg);assert.ok(ratio>=4.5,'Rasio kontras avatar '+ratio.toFixed(2)+':1 di bawah 4,5:1.');
 return {foreground:fg,background:bg,contrast_ratio:Math.round(ratio*100)/100,minimum:4.5,scope:'Perhitungan warna sRGB dari CSS; bukan pemindaian browser atau sertifikasi aksesibilitas seluruh UI.'};
});
const report={title:'Uji Regresi Temuan Audit SLR_07',executed_at:new Date().toISOString(),node_version:process.version,method:'Node.js: eksekusi handler klik pada stub DOM dan perhitungan kontras sRGB dari CSS.',browser_visual_qa:false,viewport_layout_retested:false,asset_sha256:{},summary:{passed:results.filter(r=>r.status==='LULUS_TEKNIS').length,failed:results.filter(r=>r.status==='GAGAL_TEKNIS').length,total:results.length},results};
for(const name of ['index.html','styles.css','app.mjs','model.mjs'])report.asset_sha256[name]=createHash('sha256').update(fs.readFileSync(path.join(assetPath,name))).digest('hex');
const index=process.argv.indexOf('--report');if(index>=0){const dest=process.argv[index+1];assert.ok(dest,'Jalur laporan wajib diisi.');fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');}
console.log(`\n${report.summary.passed}/${results.length} pemeriksaan regresi audit lulus; browser/visual QA tidak dilakukan.`);
if(report.summary.failed)process.exitCode=1;
