import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const [mode,input,out]=process.argv.slice(2);
if(!['preview','apply'].includes(mode)||!input||!out)throw Error('Use preview|apply input output-dir');
await fs.mkdir(out,{recursive:true});
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(input));
const token=w.worksheets.getItem('Token');
if(token.getRange('A531:D531').values[0].join('|')!=='FINAL083-NON_EVENT-01|7|peserta|O')throw Error('First source label does not match the approved correction');
if(token.getRange('A574:D574').values[0].join('|')!=='FINAL083-NON_EVENT-03|14|gempa|O')throw Error('Second source label does not match the approved correction');
if(mode==='apply'){
 token.getRange('D531').values=[['OFFICER-ARG']];
 token.getRange('D574').values=[['FALSE-EVENT']];
 w.recalculate();
 const start=w.worksheets.getItem('Mulai');
 if(start.getRange('B9:B12').values.map(x=>x[0]).join('|')!=='50|0|0|685')throw Error('Review counts changed unexpectedly');
 if(start.getRange('B14').values[0][0]!=='SIAP VALIDASI')throw Error('Approved workbook not ready');
 const scan=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:2000});
 await fs.writeFile(`${out}/formula_scan.ndjson`,scan.ndjson);
 const xlsx=await SpreadsheetFile.exportXlsx(w);
 await xlsx.save(`${out}/Review_Penerimaan_Akhir_SLR09_v0.8.3_Final_Disetujui.xlsx`);
}
for(const [sheetName,range,label] of [['Token','A526:D535','peserta'],['Token','A562:D576','negasi_gempa'],['Mulai','A5:C14','status']]){
 const p=await w.render({sheetName,range,scale:1,format:'png'});
 await fs.writeFile(`${out}/${mode}_${label}.png`,new Uint8Array(await p.arrayBuffer()));
}
console.log(JSON.stringify({mode,output:out}));
