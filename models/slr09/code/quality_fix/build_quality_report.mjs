import fs from 'node:fs/promises';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const [input, outputDir] = process.argv.slice(2);
if (!input || !outputDir) throw new Error('Usage: builder report_data.json outputDir');
const data=JSON.parse(await fs.readFile(input,'utf8'));
await fs.mkdir(outputDir,{recursive:true});
const wb=Workbook.create();
const summary=wb.worksheets.add('Rangkuman');
const errors=wb.worksheets.add('Kesalahan SENA');
const fields=wb.worksheets.add('Perubahan Field');
const notebooks=wb.worksheets.add('Notebook');
const review=wb.worksheets.add('Review Data');
const sheets=[summary,errors,fields,notebooks,review];
const navy='#18344B', ink='#172B3A', muted='#526372';
function style(sheet,range){
 sheet.showGridLines=false;
 sheet.getRange(range).format.font={name:'Arial',size:10,color:ink};
 sheet.getRange(range).format.verticalAlignment='center';
 sheet.getRange(range).format.rowHeight=24;
}
function header(sheet,range){sheet.getRange(range).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',rowHeight:30};}
function title(sheet,text){sheet.getRange('A2').values=[[text]];sheet.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:ink};sheet.getRange('A2:F2').format.borders={bottom:{style:'thin',color:'#A9BBC9'}};}
style(summary,'A1:F39');title(summary,'SLR_09: hasil perbaikan');summary.tabColor=navy;
for (const [col,width] of Object.entries({A:39,B:18,C:18,D:18,E:15,F:22})) summary.getRange(`${col}1:${col}39`).format.columnWidth=width;
summary.getRange('A4').values=[['50 narasi lama: pemeriksaan regresi setelah perbaikan, bukan uji akhir independen.']];
summary.getRange('A5').values=[['Target tetap. Cutoff confidence 0,95. Hasil metrik tidak memberi persetujuan mutu otomatis.']];
summary.getRange('A4:F5').format.font={name:'Arial',size:10,color:muted,italic:true};
summary.getRange('A8:F8').values=[['Penilaian','Sebelum','Sesudah','Target','Aturan','Status metrik']];header(summary,'A8:F8');
const values=data.comparison.map(x=>[x.metric,x.before,x.after,x.target,x.direction,null]);
summary.getRange(`A9:F${8+values.length}`).values=values;
summary.getRange(`B9:D${8+values.length}`).setNumberFormat('0.00%');
for(let i=0;i<values.length;i++){
 const row=9+i;summary.getRange(`F${row}`).formulas=[[`=IF(C${row}${data.comparison[i].direction}D${row},"Memenuhi","Belum")`]];
}
summary.getRange(`F9:F${8+values.length}`).conditionalFormats.add('containsText',{text:'Belum',format:{fill:'#FCE6E6',font:{color:'#9A2424',bold:true}}});
summary.getRange('A17').values=[['Validasi pengembangan: 146 narasi yang sama untuk pemilihan checkpoint']];
summary.getRange('A17').format.font={name:'Arial',size:10,bold:true,color:ink};
summary.getRange('A19:F19').values=[['Pelatihan','Macro F1','Recall NON_EVENT','Recall kejadian min.','Epoch terbaik','Target NE']];header(summary,'A19:F19');
summary.getRange(`A20:F${19+data.development.length}`).values=data.development.map(x=>[x.name,x.macro_f1,x.non_event_recall,x.min_event_recall,x.best_epoch,.90]);
summary.getRange(`B20:D${19+data.development.length}`).setNumberFormat('0.00%');
summary.getRange(`F20:F${19+data.development.length}`).setNumberFormat('0.00%');
summary.getRange('A24').values=[['24 narasi tambahan: label usulan asisten, tidak direview manusia, tidak dipakai memilih model.']];
summary.getRange('A24').format.font={name:'Arial',size:10,italic:true,color:muted};
summary.getRange('A26:D26').values=[['Pemeriksaan tambahan','Jumlah','Macro F1','Recall NON_EVENT']];header(summary,'A26:D26');
summary.getRange('A27:D27').values=[['Inferensi sekali jalan',data.fresh.records,data.fresh.macro_f1,data.fresh.non_event_recall]];
summary.getRange('C27:D27').setNumberFormat('0.00%');
summary.getRange('A29').values=[['Recall kejadian terendah (24)']];
summary.getRange('C29:D29').values=[[data.fresh.min_event_recall,.80]];
summary.getRange('C29:D29').setNumberFormat('0.00%');
summary.getRange('F29').formulas=[['=IF(C29>=D29,"Memenuhi","Belum")']];
summary.getRange('F29').conditionalFormats.add('containsText',{text:'Belum',format:{fill:'#FCE6E6',font:{color:'#9A2424',bold:true}}});
summary.getRange('A30:B30').values=[['Pemeriksaan kontrak kode',data.tests]];
summary.getRange('A31:B31').values=[['Status SLR_09',data.status]];
summary.getRange('A33').values=[[data.next_action]];
summary.getRange('A34').values=[['Perbandingan dengan ZIP repositori sebelumnya ditunda sesuai permintaan.']];
summary.getRange('A33:F34').format.font={name:'Arial',size:10,color:muted};
summary.getRange('A37').values=[['Angka field: tepat untuk acuan nonkosong; isi berlebih dihitung hanya pada acuan kosong.']];
summary.getRange('A37').format.font={name:'Arial',size:10,italic:true,color:muted};

function detailSheet(sheet,titleText,headers,rows,widths,heights){
 const end=String.fromCharCode(64+headers.length),last=rows.length+5;
 style(sheet,`A1:${end}${Math.max(last,6)}`);title(sheet,titleText);
 sheet.getRange(`A5:${end}5`).values=[headers];header(sheet,`A5:${end}5`);
 if(rows.length) sheet.getRange(`A6:${end}${last}`).values=rows;
 widths.forEach((width,index)=>sheet.getRange(`${String.fromCharCode(65+index)}1:${String.fromCharCode(65+index)}${Math.max(last,6)}`).format.columnWidth=width);
 if(rows.length) sheet.getRange(`A6:${end}${last}`).format.rowHeight=heights;
 sheet.freezePanes.freezeRows(5);sheet.freezePanes.freezeColumns(1);
 const table=sheet.tables.add(`A5:${end}${Math.max(last,6)}`,true,sheet.name.replaceAll(' ','')+'Table');table.showBandedRows=true;
 return {end,last};
}
const erows=data.sena_errors.map(x=>[x.scope,x.id,x.text,x.gold,x.prediction,x.confidence,x.high_confidence?'Ya':'Tidak']);
const er=detailSheet(errors,'Kesalahan klasifikasi yang masih terlihat',['Sumber','ID','Narasi','Acuan','Prediksi','Confidence','Confidence ≥0,95'],erows,[22,20,90,20,20,15,24],58);
errors.getRange(`C6:C${er.last}`).format.wrapText=true;errors.getRange(`F6:F${er.last}`).setNumberFormat('0.00%');
errors.getRange('A4').values=[['Sumber membedakan data pengembangan 146, regresi 50, dan narasi tambahan berlabel asisten.']];
const frows=data.field_changes.map(x=>[x.id,x.field,JSON.stringify(x.gold),JSON.stringify(x.before),JSON.stringify(x.after),x.after_exact?'Tepat':'Berbeda']);
const fr=detailSheet(fields,'Field yang berbeda sebelum atau sesudah perbaikan',['ID','Field','Acuan manusia','Sebelum','Sesudah','Hasil sesudah'],frows,[20,23,43,43,43,20],52);
fields.getRange(`C6:E${fr.last}`).format.wrapText=true;
fields.getRange(`F6:F${fr.last}`).conditionalFormats.add('containsText',{text:'Berbeda',format:{fill:'#FCE6E6',font:{color:'#9A2424'}}});
fields.getRange('A4').values=[['Sumber: acuan manusia 50 narasi dan hasil inferensi. [] atau null berarti kosong.']];
const nrows=data.notebooks.map(x=>[x.name,x.usage,x.execution,x.scope]);
const nr=detailSheet(notebooks,'Rekap notebook yang digunakan',['Notebook','Kegunaan','Pelaksanaan','Batas hasil'],nrows,[67,49,34,77],72);
notebooks.getRange(`A6:D${nr.last}`).format.wrapText=true;
notebooks.getRange('A4').values=[['Notebook 11, 11b dan 12 dijalankan di sini. Notebook 09 dan 10 dicatat sebagai bukti historis.']];
const rr=detailSheet(review,'Review label untuk penambahan data pengembangan',['ID','Narasi','Label sumber','Kelas reviewer','Status','Catatan','Asal label'],
 data.review_records.map(x=>[x.id,x.text,x.gold_label,null,'PENDING',null,x.origin]),[21,92,22,22,18,56,36],65);
review.getRange(`B6:B${rr.last}`).format.wrapText=true;
review.getRange(`D6:F${rr.last}`).format.fill='#FFF2CC';
review.getRange(`D6:D${rr.last}`).dataValidation={rule:{type:'list',values:['FLOOD','EARTHQUAKE','FIRE','ACCIDENT','NON_EVENT']}};
review.getRange(`E6:E${rr.last}`).dataValidation={rule:{type:'list',values:['PENDING','APPROVED','DEFERRED']}};
review.getRange('A3').values=[['16 kasus development dan 24 usulan asisten. Data ini sudah dilihat; review tidak menjadikannya test akhir baru.']];
review.getRange('A4').values=[['Reviewer']];review.getRange('B4').format.fill='#FFF2CC';

// Boundary check in the calculation engine; restore the recorded result.
const original=summary.getRange('C9').values[0][0];
summary.getRange('C9').values=[[.849]];if(summary.getRange('F9').values[0][0]!=='Belum')throw new Error('Boundary .849 failed');
summary.getRange('C9').values=[[.85]];if(summary.getRange('F9').values[0][0]!=='Memenuhi')throw new Error('Boundary .85 failed');
summary.getRange('C9').values=[[original]];
wb.recalculate();
const inspection=await wb.inspect({kind:'table',range:'Rangkuman!A8:F14',include:'values,formulas',tableMaxRows:7,tableMaxCols:6,maxChars:4500});
await fs.writeFile(`${outputDir}/workbook_inspection.ndjson`,inspection.ndjson);
const bad=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:2000});
await fs.writeFile(`${outputDir}/formula_error_scan.ndjson`,bad.ndjson);
for(const [sheet,range,label] of [[review,'A1:G9','review']]){
 const blob=await wb.render({sheetName:sheet.name,range,scale:1.4,format:'png'});
 await fs.writeFile(`${outputDir}/preview_${label}.png`,new Uint8Array(await blob.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(`${outputDir}/SLR09_Hasil_Perbaikan_v0.5.xlsx`);
console.log(JSON.stringify({file:`${outputDir}/SLR09_Hasil_Perbaikan_v0.5.xlsx`,sheets:5,classification_errors:erows.length,field_rows:frows.length,boundary_checks_passed:true}));
