import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import configure from '../vite.config.js';

const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"></svg>';
function fixture(run) {
  const root = mkdtempSync(join(tmpdir(),'silar-pwa-assets-'));
  const cwd = process.cwd();
  function put(name, content) { const path=join(root,name);mkdirSync(dirname(path),{recursive:true});writeFileSync(path,content); }
  function manifest(icons) { put('public/manifest.webmanifest',JSON.stringify({name:'SILAR test',icons})); }
  function generate() {
    process.chdir(root);
    const plugin = configure({mode:'test'}).plugins.find(value=>value.name==='silar-private-safe-pwa');
    const warnings=[],emitted=[];
    plugin.generateBundle.call({warn:value=>warnings.push(value),emitFile:value=>emitted.push(value)}, {}, {'assets/app.js':{type:'chunk',code:'test'}});
    const worker=emitted.find(value=>value.fileName==='sw.js').source;
    const assets=JSON.parse(worker.match(/const ASSETS = (.*);/)[1]);
    const version=worker.match(/const CACHE = '([^']+)';/)[1];
    return {warnings,assets,version};
  }
  try { put('index.html','<html lang="id"></html>');run({put,manifest,generate}); }
  finally { process.chdir(cwd);rmSync(root,{recursive:true,force:true}); }
}

test('Custom manifest icons work without the old icons directory, including a filename with spaces',()=>fixture(({put,manifest,generate})=>{
  put('public/custom-icons/logo final.svg',svg);
  put('public/brand/silar-logo.svg',svg);
  manifest([{src:'/custom-icons/logo%20final.svg',sizes:'any',type:'image/svg+xml'}]);
  const result=generate();
  assert.deepEqual(result.warnings,[]);
  assert(result.assets.includes('/custom-icons/logo%20final.svg'));
  assert(result.assets.includes('/brand/silar-logo.svg'));
  assert(!result.assets.some(value=>value.includes('icon-192.png')||value.includes('icon-512.png')));
}));

test('A stale icon reference warns without ENOENT or precaching a missing file; API/private data stays out',()=>fixture(({put,manifest,generate})=>{
  put('public/api/v1/evidence/private.svg',svg);
  put('public/private/report.json','{"private":true}');
  put('public/brand/settings.json','{"notAnAsset":true}');
  manifest([{src:'/icons/icon-192.png'},{src:'/api/v1/evidence/private.svg'}]);
  const result=generate();
  assert.equal(result.warnings.length,1);
  assert.match(result.warnings[0],/manifest.webmanifest/);
  assert(!result.assets.includes('/icons/icon-192.png'));
  assert(!result.assets.some(value=>value.startsWith('/api/')||value.includes('private')||value.endsWith('settings.json')));
}));

test('Changing icon bytes or HTML changes the UI cache version without renaming the asset',()=>fixture(({put,manifest,generate})=>{
  put('public/brand/silar.svg',svg);manifest([{src:'/brand/silar.svg'}]);
  const first=generate();
  put('public/brand/silar.svg',svg.replace('192 192','512 512'));
  const second=generate();
  assert.notEqual(first.version,second.version);
  put('index.html','<html lang="id"><title>SILAR updated</title></html>');
  assert.notEqual(second.version,generate().version);
}));
