import test from 'node:test';
import assert from 'node:assert/strict';
import {chooseRecordingType, recordingFileInfo} from '../src/audio.js';

test('Recorder mendahulukan WebM dengan codec Opus', () => {
  assert.equal(chooseRecordingType({isTypeSupported: () => true}), 'audio/webm;codecs=opus');
});
test('Recorder memakai AAC atau MP4 generik ketika WebM tidak tersedia', () => {
  assert.equal(chooseRecordingType({isTypeSupported: x => x.includes('mp4a.40.2')}), 'audio/mp4;codecs=mp4a.40.2');
  assert.equal(chooseRecordingType({isTypeSupported: x => x === 'audio/mp4'}), 'audio/mp4');
});
test('Tidak ada fallback OGG atau format default yang tidak diketahui', () => {
  assert.equal(chooseRecordingType({isTypeSupported: x => x.includes('ogg')}), '');
  assert.equal(chooseRecordingType(undefined), '');
  assert.equal(chooseRecordingType({isTypeSupported: () => {throw new Error();}}), '');
});
test('Nama dan MIME mengikuti keluaran rekaman yang sebenarnya', () => {
  assert.equal(recordingFileInfo('audio/webm;codecs=opus').name, 'rekaman.webm');
  assert.deepEqual(recordingFileInfo('audio/mp4;codecs="mp4a.40.2"'), {mime:'audio/mp4;codecs="mp4a.40.2"',name:'rekaman.mp4'});
  assert.equal(recordingFileInfo('audio/mp4').name, 'rekaman.mp4');
});
test('Keluaran OGG, Vorbis, ALAC, video dan MIME kosong tidak disamarkan', () => {
  for (const mime of ['audio/ogg;codecs=opus','audio/webm;codecs=vorbis','audio/mp4;codecs=alac','video/mp4','']) assert.throws(() => recordingFileInfo(mime));
});
