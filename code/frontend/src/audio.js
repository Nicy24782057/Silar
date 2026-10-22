export const RECORDING_TYPES = Object.freeze([
  'audio/webm;codecs=opus',
  'audio/mp4;codecs=mp4a.40.2',
  'audio/mp4;codecs=mp4a.40.5',
  'audio/mp4',
]);

export function chooseRecordingType(Recorder) {
  if (typeof Recorder?.isTypeSupported !== 'function') return '';
  return RECORDING_TYPES.find(type => {
    try { return Recorder.isTypeSupported(type); } catch { return false; }
  }) || '';
}

export function recordingFileInfo(value) {
  const mime = String(value || '').toLowerCase().trim();
  const type = mime.split(';')[0].trim();
  const codecs = mime.match(/codecs\s*=\s*"?([^";]+)/)?.[1]?.split(',').map(x => x.trim());
  if (type === 'audio/webm' && (!codecs || codecs.every(x => x === 'opus'))) {
    return {mime, name: 'rekaman.webm'};
  }
  if (type === 'audio/mp4' && (!codecs || codecs.every(x => /^mp4a\.40\.\d+$/.test(x)))) {
    return {mime, name: 'rekaman.mp4'};
  }
  throw new Error('Format rekaman browser belum didukung. Unggah WAV PCM, MP3, WebM/Opus, atau M4A/MP4-AAC tanpa video.');
}
