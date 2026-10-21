import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';

const [source,input,out]=process.argv.slice(2);
if(!source||!input||!out)throw new Error('Usage: update_report.mjs source.xlsx report_data.json output-directory');
const d=JSON.parse(await fs.readFile(input,'utf8'));
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(source));
const s=wb.worksheets.getItem('Rangkuman');
const er=wb.worksheets.getItem('Kesalahan SENA');
const nb=wb.worksheets.getItem('Notebook');
const review=wb.worksheets.getItem('Review Data');
const originalReview=JSON.stringify(review.getRange('A1:G45').values);
const originalFields=JSON.stringify(wb.worksheets.getItem('Perubahan Field').getUsedRange().values);
const navy='#18344B',ink='#172B3A',muted='#526372';
function header(sheet,range){sheet.getRange(range).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',rowHeight:30};}
function note(sheet,address,text){sheet.getRange(address).values=[[text]];sheet.getRange(address).format.font={name:'Arial',size:10,color:muted,italic:true};}
s.getRange('A2').values=[['SLR_09: hasil perbaikan v0.7']];
s.getRange('C9:C14').values=d.comparison.map(x=>[x.after]);
const dev=d.latest_development;
s.getRange('A23:F23').values=[[dev.name,dev.macro_f1,dev.non_event_recall,dev.min_event_recall,dev.best_epoch,.90]];
s.getRange('B23:D23').setNumberFormat('0.00%');s.getRange('F23').setNumberFormat('0.00%');
note(s,'A24','Development asisten 74 dipakai seleksi. Diagnostik baru 50 belum direview manusia.');
s.getRange('A26:F26').values=[['Diagnostik baru v0.7','Jumlah','Macro F1','Recall NON_EVENT','Recall nyata min.','Status target']];header(s,'A26:F26');
s.getRange('A27:F27').values=[['Label usulan asisten',50,d.fresh.macro_f1,d.fresh.non_event_recall,d.fresh.min_event_recall,null]];
s.getRange('C27:E27').setNumberFormat('0.00%');
s.getRange('F27').formulas=[['=IF(AND(C27>=D9,D27>=D10,E27>=D29),"Memenuhi","Belum")']];
s.getRange('F27').format.horizontalAlignment='center';
s.getRange('F27').conditionalFormats.add('containsText',{text:'Belum',format:{fill:'#FCE6E6',font:{color:'#9A2424',bold:true}}});
s.getRange('A29').values=[['Recall kejadian terendah (baru 50)']];s.getRange('C29').formulas=[['=E27']];
s.getRange('B30').values=[[d.tests]];s.getRange('B31').values=[[d.status]];
note(s,'A33',d.next_action);
s.getRange('A39:F54').format.font={name:'Arial',size:10,color:ink};s.getRange('A39:F54').format.rowHeight=24;
note(s,'A39','Status target merangkum metrik label usulan. Penerimaan mutu belum diberikan.');
s.getRange('A41').values=[['Riwayat diagnostik dan development']];s.getRange('A41').format.font={name:'Arial',size:10,bold:true,color:ink};
s.getRange('A43:F43').values=[['Percobaan dan data','Jumlah','Macro F1','Recall NON_EVENT','Recall nyata min.','Peran data kini']];header(s,'A43:F43');
s.getRange('A44:F47').values=d.history;s.getRange('C44:E47').setNumberFormat('0.00%');
s.getRange('F44:F47').format.horizontalAlignment='center';
note(s,'A49','Target tidak diturunkan. Set yang dipakai memperbaiki model menjadi development.');
s.getRange('A51').values=[['Status APPROVED (dari 40)']];s.getRange('B51').formulas=[['=COUNTIF(\'Review Data\'!E6:E45,"APPROVED")']];s.getRange('E51').values=[['PENDING']];s.getRange('F51').formulas=[['=COUNTIF(\'Review Data\'!E6:E45,"PENDING")']];
note(s,'A53','Review Data tetap berisi 40 baris asli. Reviewer dan keputusan diisi oleh manusia.');

er.getRange('A4').values=[['Kesalahan kandidat v0.7. Acuan tambahan asisten belum disetujui manusia.']];
const err=d.sena_errors.map(x=>[x.scope,x.id,x.text,x.gold,x.prediction,x.confidence,x.high_confidence?'Ya':'Tidak']);
const oldErrors=er.tables.items[0];
er.getRange('A6:G25').clear({applyTo:'contents'});
if(err.length>20)oldErrors.rows.add(null,err.slice(20));
if(err.length)er.getRange(`A6:G${5+err.length}`).values=err;
const lastError=Math.max(25,5+err.length);
er.getRange(`C6:C${lastError}`).format.wrapText=true;er.getRange(`A6:G${lastError}`).format.rowHeight=65;
er.getRange(`F6:F${lastError}`).setNumberFormat('0.00%');

nb.getRange('A4').values=[['Notebook 11–16 dijalankan di sini lewat sel CPython. Notebook 09–10 adalah bukti historis.']];
const notebookRows=d.notebooks.map(x=>[x.name,x.usage,x.execution,x.scope]);
if(notebookRows.length>5)nb.tables.items[0].rows.add(null,notebookRows.slice(5));
nb.getRange(`A6:D${5+notebookRows.length}`).values=notebookRows;
nb.getRange(`A11:D${5+notebookRows.length}`).format.font={name:'Arial',size:10,color:ink};
nb.getRange(`A11:D${5+notebookRows.length}`).format.verticalAlignment='center';
nb.getRange(`A6:D${5+notebookRows.length}`).format.wrapText=true;
nb.getRange(`A11:D${5+notebookRows.length}`).format.rowHeight=72;

const fresh=wb.worksheets.add('Diagnostik Baru');fresh.showGridLines=false;
fresh.getRange('A1:G55').format={font:{name:'Arial',size:10,color:ink},verticalAlignment:'center',rowHeight:24};
fresh.getRange('A2').values=[['Diagnostik baru v0.7: 50 narasi']];fresh.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:ink};
fresh.getRange('A2:G2').format.borders={bottom:{style:'thin',color:'#A9BBC9'}};
note(fresh,'A3','Acuan usulan asisten. Dibekukan sebelum pelatihan. Tidak digunakan memilih kandidat v0.7.');
note(fresh,'A4','Perbandingan terhadap usulan ini bukan persetujuan label atau penerimaan mutu manusia.');
fresh.getRange('A5:G5').values=[['ID','Narasi','Acuan usulan','Prediksi','Confidence','Perbandingan','Konteks']];header(fresh,'A5:G5');
fresh.getRange('A6:G55').values=d.new_rows.map(x=>[x.id,x.text,x.proposed_label,x.prediction,x.confidence,null,x.family]);
fresh.getRange('F6:F55').formulas=d.new_rows.map((_,i)=>[`=IF(C${i+6}=D${i+6},"Sesuai usulan","Berbeda")`]);
for(const [col,width] of Object.entries({A:29,B:96,C:22,D:22,E:16,F:22,G:25}))fresh.getRange(`${col}1:${col}55`).format.columnWidth=width;
fresh.getRange('B6:B55').format.wrapText=true;fresh.getRange('G6:G55').format.wrapText=true;fresh.getRange('A6:G55').format.rowHeight=70;
fresh.getRange('E6:E55').setNumberFormat('0.00%');
fresh.getRange('F6:F55').conditionalFormats.add('containsText',{text:'Berbeda',format:{fill:'#FCE6E6',font:{color:'#9A2424',bold:true}}});
fresh.tables.add('A5:G55',true,'DiagnostikBaruV07Table');fresh.freezePanes.freezeRows(5);fresh.freezePanes.freezeColumns(1);

// Exercise both sides of the existing status thresholds, then restore all data.
const fOriginal=s.getRange('C27:E27').values;
s.getRange('C27:E27').values=[[.85,.90,.80]];
if(s.getRange('F27').values[0][0]!=='Memenuhi')throw new Error('Inclusive target boundary failed');
s.getRange('E27').values=[[.7999]];
if(s.getRange('F27').values[0][0]!=='Belum')throw new Error('Event recall boundary failed');
s.getRange('C27:E27').values=[[.85,.8999,.80]];
if(s.getRange('F27').values[0][0]!=='Belum')throw new Error('NON_EVENT boundary failed');
s.getRange('C27:E27').values=fOriginal;
if(JSON.stringify(review.getRange('A1:G45').values)!==originalReview)throw new Error('Human review cells changed');
if(JSON.stringify(wb.worksheets.getItem('Perubahan Field').getUsedRange().values)!==originalFields)throw new Error('Unrelated field detail changed');
wb.recalculate();
await fs.mkdir(out,{recursive:true});
const check=await wb.inspect({kind:'table',range:'Rangkuman!A19:F31',include:'values,formulas',tableMaxRows:13,tableMaxCols:6,maxChars:6500});
await fs.writeFile(`${out}/workbook_inspection_v07.ndjson`,check.ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:2000});
await fs.writeFile(`${out}/formula_error_scan_v07.ndjson`,errors.ndjson);
const isMet=d.fresh.macro_f1>=.85&&d.fresh.non_event_recall>=.90&&d.fresh.min_event_recall>=.80;
if(s.getRange('F27').values[0][0]!== (isMet?'Memenuhi':'Belum'))throw new Error('Final status formula disagrees with actual metrics');
for(const [sheet,range,name] of [[s,'A1:F34','summary'],[s,'A39:F53','history'],[nb,'A1:D15','notebooks'],[er,'A1:G10','errors'],[fresh,'A1:G10','diagnostic']]){
 const png=await wb.render({sheetName:sheet.name,range,scale:1,format:'png'});
 await fs.writeFile(`${out}/preview_v07_${name}.png`,new Uint8Array(await png.arrayBuffer()));
}
const exported=await SpreadsheetFile.exportXlsx(wb);await exported.save(`${out}/SLR09_Hasil_Perbaikan_v0.7.xlsx`);
console.log(JSON.stringify({file:`${out}/SLR09_Hasil_Perbaikan_v0.7.xlsx`,unchanged_review_rows:40,new_diagnostic_rows:50,boundaries_checked:true,diagnostic_targets_met:isMet}));
