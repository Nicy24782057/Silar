import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { makeServiceWorker } from './tools/service-worker.js';

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxy = {'/api': {target: env.BACKEND_URL || 'http://localhost:8001', changeOrigin: false}};
  return {
    plugins: [vue(), {
      name: 'silar-private-safe-pwa',
      generateBundle(_, bundle) {
        const assets = ['/', '/index.html', '/manifest.webmanifest', '/icons/icon-192.png', '/icons/icon-512.png',
          ...Object.keys(bundle).map(name => '/' + name)];
        const hash = createHash('sha256').update(JSON.stringify(assets));
        for (const name of ['manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png']) hash.update(readFileSync('public/' + name));
        const version = hash.digest('hex').slice(0, 16);
        this.emitFile({type: 'asset', fileName: 'sw.js', source: makeServiceWorker(assets, version)});
      }
    }],
    server: {proxy}, preview: {proxy}, build: {target: 'es2022', sourcemap: false}
  };
});
