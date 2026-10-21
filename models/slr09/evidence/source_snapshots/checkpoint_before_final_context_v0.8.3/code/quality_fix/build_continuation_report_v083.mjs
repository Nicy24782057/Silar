import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const [run, output] = process.argv.slice(2);
if (!run || !output) throw Error('Use: builder RUN_DIRECTORY OUTPUT_DIRECTORY');
const read = async name => JSON.parse(await fs.readFile(`${run}/${name}`, 'utf8'));
const baseline = await read('baseline_evaluation.json');
const history = await read('training_history.json');
const selected = await read('best_selection.json');
const state = await read('run_state.json');
if (!['SUCCEEDED', 'FAILED', 'NO_FEASIBLE_CANDIDATE'].includes(state.status)) throw Error('Training is unfinished');
const names = Object.keys(selected.metrics);
const humanNames = {
  human130: 'Manusia 130', original146: 'Label sumber 146', adjudicated145: 'Adjudikasi 145',
  scope50: 'Usulan v0.6: 50', seen_v07_50: 'Usulan v0.7: 50',
  human_regression50: 'Regresi manusia: 50', FINAL081: 'FINAL081', FINAL082: 'FINAL082',
  context40_now_training: 'Konteks tambahan: 40',
};
const ink = '#173044', navy = '#203F57', gray = '#526575', amber = '#FFF1CE';
const workbook = Workbook.create();
const summary = workbook.worksheets.add('Hasil');
const epochs = workbook.worksheets.add('Putaran');
const errors = workbook.worksheets.add('Kesalahan');
function format(sheet, address) {
  sheet.showGridLines = false;
  sheet.getRange(address).format = { font: { name: 'Arial', size: 10, color: ink },
    rowHeight: 25, verticalAlignment: 'center' };
}
function widths(sheet, columns, last) {
  for (const [column, width] of Object.entries(columns)) sheet.getRange(`${column}1:${column}${last}`).format.columnWidth = width;
}
function title(sheet, text, last) {
  sheet.getRange('A2').values = [[text]];
  sheet.getRange('A2').format.font = { name: 'Arial', size: 15, bold: true, color: ink };
  sheet.getRange(`A2:${last}2`).format.borders = { bottom: { style: 'thin', color: '#AABCC9' } };
}
function note(sheet, address, text) {
  sheet.getRange(address).values = [[text]];
  sheet.getRange(address).format.font = { name: 'Arial', size: 10, color: gray, italic: true };
}
function header(sheet, address) {
  sheet.getRange(address).format = { fill: navy, font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' },
    rowHeight: 36, horizontalAlignment: 'center', verticalAlignment: 'center', wrapText: true };
}
function highlight(sheet, address) {
  sheet.getRange(address).conditionalFormats.add('containsText', { text: 'Belum',
    format: { fill: '#FCE6E6', font: { bold: true, color: '#9A2424' } } });
}
function data(metrics) {
  const ne = metrics.per_class.NON_EVENT;
  return { n: Object.values(metrics.per_class).reduce((s, c) => s + c.support, 0),
    macro: metrics.macro_f1, neCorrect: Math.round(ne.recall * ne.support), neN: ne.support,
    minEvent: Math.min(...Object.entries(metrics.per_class).filter(([name]) => name !== 'NON_EVENT').map(([, c]) => c.recall)),
    accuracy: metrics.accuracy };
}

format(summary, 'A1:M28');
widths(summary, { A:29, B:11, C:15, D:17, E:17, F:20, G:12, H:12, I:16, J:15, K:19, L:17, M:24 }, 28);
summary.tabColor = navy;
title(summary, 'SILAR: hasil pelatihan SENA v0.8.3', 'M');
summary.getRange('A4:B6').values = [['Status SLR_09', 'IN REVIEW'], ['Putaran diagnostik terpilih', selected.epoch], ['Status regresi', null]];
summary.getRange('B4').format.fill = amber;
summary.getRange('A8').values = [['Target: macro F1 >=85%, recall NON_EVENT >=90%, recall tiap kejadian >=80%.']];
note(summary, 'A9', 'Seluruh data di bawah sudah dipakai untuk training atau pemilihan. Ini hasil pengembangan.');
note(summary, 'A10', 'Kolom terpilih mengikuti pemilihan diagnostik; tidak menyatakan penerimaan model produksi.');
summary.getRange('A12:M12').values = [['Kelompok data','Narasi','F1 awal','F1 terpilih','Recall NON_EVENT','Recall kejadian min','NE benar','NE total','Kontras salah','Akurasi','Target angka','Kontras','Status kelompok']];
header(summary, 'A12:M12');
summary.getRange(`A13:M${12+names.length}`).values = names.map(name => {
  const m = data(selected.metrics[name]);
  return [humanNames[name], m.n, baseline.metrics[name].macro_f1, m.macro, null, m.minEvent,
    m.neCorrect, m.neN, selected.contrast_errors[name].length, m.accuracy, null, null, null];
});
for (let index = 0; index < names.length; index++) {
  const r = index + 13;
  summary.getRange(`E${r}`).formulas = [[`=IF(H${r}=0,"n.a.",G${r}/H${r})`]];
  summary.getRange(`K${r}`).formulas = [[`=IF(AND(D${r}>=0.85,E${r}>=0.9,F${r}>=0.8),"Lulus","Belum")`]];
  summary.getRange(`L${r}`).formulas = [[`=IF(I${r}=0,"Lulus","Belum")`]];
  const accuracy = names[index] === 'context40_now_training' ? `,J${r}=1` : '';
  summary.getRange(`M${r}`).formulas = [[`=IF(AND(K${r}="Lulus",L${r}="Lulus"${accuracy}),"Lulus","Belum")`]];
}
summary.getRange('B6').formulas = [[`=IF(COUNTIFS(M13:M${12+names.length},"Belum")=0,"Memenuhi","Belum")`]];
summary.getRange(`C13:F${12+names.length}`).setNumberFormat('0.00%');
summary.getRange(`J13:J${12+names.length}`).setNumberFormat('0.00%');
summary.getRange(`B13:B${12+names.length}`).setNumberFormat('0');
summary.getRange(`G13:I${12+names.length}`).setNumberFormat('0');
summary.getRange(`K13:M${12+names.length}`).format.horizontalAlignment = 'center';
highlight(summary, `K13:M${12+names.length}`);
highlight(summary, 'B6');
note(summary, 'A24', 'Konteks tambahan harus benar 40/40, di samping target angka dan seluruh kontras pada data lain.');
note(summary, 'A25', 'Kelompok data saling beririsan. Jumlah kesalahan antarkelompok tidak dijumlahkan sebagai narasi unik.');
note(summary, 'A26', 'NARA tidak dilatih ulang. Cutoff confidence tetap 0,95. Uji penerimaan baru belum dijalankan.');

const stages = [{ label:'Awal', ...baseline }, ...history.map(row => ({ label:`Putaran ${row.epoch}`, ...row }))];
const epochRows = stages.flatMap(stage => names.map(name => {
  const m = data(stage.metrics[name]);
  return [stage.label, humanNames[name], m.macro, m.neCorrect, m.neN, null, m.minEvent,
    m.accuracy, stage.contrast_errors[name].length, null, null];
}));
const epochLast = epochRows.length + 5;
format(epochs, `A1:K${epochLast}`);
widths(epochs, { A:18, B:29, C:17, D:13, E:13, F:18, G:21, H:17, I:16, J:20, K:24 }, epochLast);
title(epochs, 'Perkembangan tiap putaran', 'K');
note(epochs, 'A3', 'Sumber: baseline_evaluation.json dan training_history.json dari eksekusi aktual notebook 26.');
note(epochs, 'A4', 'Label sumber lama tetap dipertahankan; semua kelompok ini sudah dilihat oleh proses pelatihan atau seleksi.');
epochs.getRange('A5:K5').values = [['Tahap','Kelompok data','Macro F1','NE benar','NE total','Recall NON_EVENT','Recall kejadian min','Akurasi','Kontras salah','Target angka','Semua syarat kelompok']];
header(epochs, 'A5:K5');
epochs.getRange(`A6:K${epochLast}`).values = epochRows;
for (let i = 0; i < epochRows.length; i++) {
  const r = i + 6;
  epochs.getRange(`F${r}`).formulas = [[`=IF(E${r}=0,"n.a.",D${r}/E${r})`]];
  epochs.getRange(`J${r}`).formulas = [[`=IF(AND(C${r}>=0.85,F${r}>=0.9,G${r}>=0.8),"Lulus","Belum")`]];
  const accuracy = names[i % names.length] === 'context40_now_training' ? `,H${r}=1` : '';
  epochs.getRange(`K${r}`).formulas = [[`=IF(AND(J${r}="Lulus",I${r}=0${accuracy}),"Lulus","Belum")`]];
}
epochs.getRange(`C6:C${epochLast}`).setNumberFormat('0.00%');
epochs.getRange(`F6:H${epochLast}`).setNumberFormat('0.00%');
epochs.getRange(`J6:K${epochLast}`).format.horizontalAlignment = 'center';
highlight(epochs, `J6:K${epochLast}`);
epochs.tables.add(`A5:K${epochLast}`, true, 'TrainingStagesV083');
epochs.freezePanes.freezeRows(5);
epochs.freezePanes.freezeColumns(2);

const errorRows = [];
for (const name of names) {
  const predictions = await read(`predictions_${name}.json`);
  for (const row of predictions) {
    const [prediction, confidence] = Object.entries(row.probabilities).sort((a,b) => b[1]-a[1])[0];
    if (prediction !== row.gold) errorRows.push([humanNames[name], row.id, row.text, row.gold,
      prediction, confidence, confidence < .95 ? 'Ya' : 'Tidak',
      name === 'context40_now_training' ? 'Usulan asisten, dipakai training' : 'Acuan lama, dipakai training/seleksi']);
  }
}
const errorLast = Math.max(6, errorRows.length + 5);
format(errors, `A1:H${errorLast}`);
widths(errors, { A:28, B:32, C:84, D:19, E:19, F:17, G:17, H:35 }, errorLast);
title(errors, 'Kesalahan pada checkpoint diagnostik terpilih', 'H');
note(errors, 'A3', 'Probabilitas berasal dari keluaran model aktual. Semua kesalahan tetap ditampilkan.');
note(errors, 'A4', 'Kelompok dapat memuat narasi yang sama; angka pada tab ini bukan jumlah narasi unik.');
errors.getRange('A5:H5').values = [['Kelompok','ID','Narasi','Acuan kelas','Prediksi SENA','Confidence','Flag <0,95','Asal/acuan']];
header(errors, 'A5:H5');
if (errorRows.length) {
  errors.getRange(`A6:H${errorLast}`).values = errorRows;
  errors.getRange(`C6:C${errorLast}`).format.wrapText = true;
  errors.getRange(`H6:H${errorLast}`).format.wrapText = true;
  errors.getRange(`A6:H${errorLast}`).format.rowHeight = 68;
  errors.getRange(`F6:F${errorLast}`).setNumberFormat('0.00%');
  errors.getRange(`G6:G${errorLast}`).format.horizontalAlignment = 'center';
  errors.tables.add(`A5:H${errorLast}`, true, 'SelectedCheckpointErrorsV083');
} else errors.getRange('A6').values = [['Tidak ada kesalahan pada data yang sudah dilihat ini.']];
errors.freezePanes.freezeRows(5);
errors.freezePanes.freezeColumns(2);

workbook.recalculate();
const formulaState = summary.getRange('B6').values[0][0] === 'Memenuhi';
if (formulaState !== selected.feasible) throw Error('Workbook status disagrees with actual selection');
const scan = await workbook.inspect({ kind:'match', searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',
  options:{ useRegex:true, maxResults:100 }, maxChars:1800 });
if (!scan.ndjson.includes('Cell search matched 0 entries.')) throw Error(scan.ndjson);
await fs.mkdir(output, { recursive:true });
await fs.writeFile(`${output}/formula_scan_v083.ndjson`, scan.ndjson);
const inspect = await workbook.inspect({ kind:'table', range:'Hasil!A4:B6', include:'values,formulas',
  tableMaxRows:4, tableMaxCols:2, maxChars:1200 });
await fs.writeFile(`${output}/summary_inspection_v083.ndjson`, inspect.ndjson);
for (const [sheetName, range, suffix] of [['Hasil','A1:M26','hasil'],['Putaran','A1:K12','putaran'],['Kesalahan',`A1:H${Math.min(errorLast,9)}`,'kesalahan']]) {
  const preview = await workbook.render({ sheetName, range, scale:1, format:'png' });
  await fs.writeFile(`${output}/SLR09_Hasil_Lanjutan_v0.8.3_${suffix}.png`, new Uint8Array(await preview.arrayBuffer()));
}
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
const filename = 'SLR09_Hasil_Lanjutan_v0.8.3_2026-10-20.xlsx';
await xlsx.save(`${output}/${filename}`);
await fs.writeFile(`${output}/workbook_verification_v083.json`, JSON.stringify({
  training_status:state.status, selected_diagnostic_epoch:selected.epoch,
  known_constraints_met:selected.feasible, groups:names.length, stage_rows:epochRows.length,
  error_rows_with_overlapping_groups:errorRows.length, formulas_match_actual_state:true,
  formula_errors:0, independent_acceptance_claimed:false, quality_acceptance_approved:false,
  filename,
}, null, 2));
console.log(JSON.stringify({ filename, known_constraints_met:selected.feasible, error_rows:errorRows.length }));
