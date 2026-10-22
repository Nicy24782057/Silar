<script setup>
import { ref, onUnmounted } from 'vue';
import { chooseRecordingType, recordingFileInfo } from '../audio';
const emit = defineEmits(['recorded']);
defineProps({disabled: Boolean});
const recording = ref(false), starting = ref(false), seconds = ref(0), error = ref('');
let recorder, stream, timer, disposed = false;

function cleanup() {
  clearInterval(timer);
  stream?.getTracks().forEach(track => track.stop());
  stream = null;
  recorder = null;
  recording.value = false;
}

async function start() {
  error.value = '';
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    error.value = 'Perekaman tidak tersedia. Unggah berkas audio atau gunakan teks/gambar.';
    return;
  }
  const mimeType = chooseRecordingType(window.MediaRecorder);
  if (!mimeType) {
    error.value = 'Browser belum mendukung rekaman WebM/Opus atau MP4/AAC. Unggah audio yang didukung atau gunakan teks/gambar.';
    return;
  }
  starting.value = true;
  try {
    stream = await navigator.mediaDevices.getUserMedia({audio: true});
    if (disposed) { cleanup(); return; }
    const current = new MediaRecorder(stream, {mimeType});
    recorder = current;
    const chunks = [];
    let failed = false;
    seconds.value = 0;
    current.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
    current.onerror = () => {
      failed = true;
      error.value = 'Rekaman gagal. Coba lagi atau unggah berkas audio yang didukung.';
      if (current.state === 'recording') current.stop();
      if (recorder === current) cleanup();
    };
    current.onstop = () => {
      if (recorder !== current) return;
      try {
        if (disposed || failed) return;
        const info = recordingFileInfo(current.mimeType || chunks[0]?.type);
        const blob = new Blob(chunks, {type: info.mime});
        if (!blob.size) throw new Error('Rekaman kosong. Coba lagi atau unggah berkas audio.');
        // The backend still checks the actual container, codec and duration,
        // including MP4 selected through a browser's generic MIME support.
        emit('recorded', new File([blob], info.name, {type: info.mime}));
      } catch (failure) { error.value = failure.message; }
      finally { cleanup(); }
    };
    current.start();
    recording.value = true;
    timer = setInterval(() => { if (++seconds.value >= 120) stop(); }, 1000);
  } catch (failure) {
    error.value = failure.name === 'NotAllowedError'
      ? 'Izin mikrofon ditolak. Izinkan mikrofon pada pengaturan situs atau unggah berkas audio.'
      : 'Mikrofon belum dapat digunakan. Periksa perangkat dan izin browser atau unggah berkas audio.';
    cleanup();
  } finally { starting.value = false; }
}

function stop() { if (recorder?.state === 'recording') recorder.stop(); }
onUnmounted(() => { disposed = true; stop(); cleanup(); });
</script>
<template>
  <div class="recorder">
    <button v-if="!recording" type="button" :disabled="disabled || starting" @click="start">{{ starting ? 'Menyiapkan mikrofon…' : '● Rekam suara' }}</button>
    <button v-else type="button" class="danger" @click="stop">■ Hentikan · {{ seconds }} detik</button>
    <small v-if="recording" role="status">Mikrofon aktif. Rekaman berhenti otomatis pada dua menit.</small>
    <small v-if="error" class="text-error" role="alert">{{ error }}</small>
  </div>
</template>
