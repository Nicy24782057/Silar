import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import { extname, isAbsolute, relative, resolve, sep } from 'node:path';
import { makeServiceWorker } from './tools/service-worker.js';

const imageTypes = new Set(['.png', '.svg', '.webp', '.ico', '.jpg', '.jpeg', '.avif']);
const uiTypes = new Set([...imageTypes, '.ttf', '.woff', '.woff2', '.otf']);
const toUrl = name => '/' + name.split('/').map(encodeURIComponent).join('/');

function publicUiFiles(root, warn) {
  const publicDir = resolve(root, 'public');
  const files = new Set(['manifest.webmanifest']);
  const localName = file => relative(publicDir, file).split(sep).join('/');
  // Brand, icon and font filenames may differ on an existing clone.
  // Only public UI assets are discovered; API/data/private directories are not scanned.
  function scan(directory) {
    if (!existsSync(directory)) return;
    for (const entry of readdirSync(directory, {withFileTypes: true})) {
      const file = resolve(directory, entry.name);
      if (entry.isDirectory()) scan(file);
      else if (entry.isFile() && uiTypes.has(extname(entry.name).toLowerCase())) files.add(localName(file));
    }
  }
  for (const directory of ['brand', 'icons', 'fonts']) scan(resolve(publicDir, directory));

  const manifest = JSON.parse(readFileSync(resolve(publicDir, 'manifest.webmanifest'), 'utf8'));
  const base = new URL('https://silar-static.invalid/manifest.webmanifest');
  for (const icon of Array.isArray(manifest.icons) ? manifest.icons : []) {
    if (!icon || typeof icon.src !== 'string') continue;
    let url, file;
    try {
      url = new URL(icon.src, base);
      if (url.origin !== base.origin) continue;
      file = resolve(publicDir, '.' + decodeURIComponent(url.pathname));
    } catch { warn('Src ikon PWA tidak dapat dibaca: ' + icon.src); continue; }
    const name = relative(publicDir, file);
    if (name === '..' || name.startsWith('..' + sep) || isAbsolute(name) || !imageTypes.has(extname(file).toLowerCase())) continue;
    if (/^(api|health)(\/|$)/i.test(localName(file))) continue;
    if (existsSync(file) && lstatSync(file).isFile()) files.add(localName(file));
    else warn('Ikon manifest belum tersedia di public/: ' + icon.src + '. Sesuaikan src ikon pada manifest.webmanifest dengan berkas logo yang dipakai.');
  }
  return [...files].sort();
}

export default defineConfig(({mode}) => {
  const root = process.cwd();
  const env = loadEnv(mode, root, '');
  const proxy = {'/api': {target: env.BACKEND_URL || 'http://localhost:8001', changeOrigin: false}};
  return {
    plugins: [vue(), {
      name: 'silar-private-safe-pwa',
      generateBundle(_, bundle) {
        const publicFiles = publicUiFiles(root, message => this.warn(message));
        const assets = [...new Set(['/', '/index.html', ...publicFiles.map(toUrl),
          ...Object.keys(bundle).sort().map(toUrl)])];
        const hash = createHash('sha256').update(JSON.stringify(assets)).update(readFileSync(resolve(root, 'index.html')));
        for (const name of publicFiles) hash.update(name).update(readFileSync(resolve(root, 'public', name)));
        const version = hash.digest('hex').slice(0, 16);
        this.emitFile({type: 'asset', fileName: 'sw.js', source: makeServiceWorker(assets, version)});
      }
    }],
    server: {proxy}, preview: {proxy}, build: {target: 'es2022', sourcemap: false}
  };
});
