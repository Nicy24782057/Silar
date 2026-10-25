import { ApiError } from './api.js';
import { validateBundle, usesGemini } from './domain.js';

export function sameEvidence(items, ids) {
  const saved = new Set(items.map(item => item.evidence?.id ?? item.id));
  return saved.size === items.length && saved.size === ids.length && new Set(ids).size === ids.length && ids.every(id => saved.has(id));
}

// Replacing a channel keeps its original items in the private server archive.
export function useSavedEvidence(selected, item) {
  const others = selected.filter(existing => existing.id !== item.id &&
    (!['TEXT', 'AUDIO'].includes(item.type) || existing.type !== item.type));
  return [...others, item];
}

export function defaultEvidence(rows, bundle) {
  let selected = (bundle?.items || []).map(item => item.evidence);
  const ordered = [...rows].sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at) || a.id.localeCompare(b.id));
  for (const item of ordered) {
    if (!bundle || Date.parse(item.created_at) > Date.parse(bundle.created_at)) selected = useSavedEvidence(selected, item);
  }
  return selected;
}

export function uploadProblem(selected, kind, values) {
  const additions = values.map((value, index) => ({id: 'pending-' + index, type: kind,
    byte_size: kind === 'TEXT' ? new TextEncoder().encode(value).length : value.size}));
  let candidate = selected;
  for (const item of additions) candidate = useSavedEvidence(candidate, item);
  return validateBundle(candidate);
}

// One explicit click prepares the immutable source snapshot, then starts
// analysis. An uncertain or failed preparation never retries either POST.
export async function analyseSavedEvidence(request, detail, items, consent, onPrepared = () => {}) {
  const problem = validateBundle(items);
  if (problem) throw new ApiError(problem, 'INVALID_PAYLOAD');
  if (usesGemini(items) && !consent) throw new ApiError('Baca informasi pemrosesan eksternal dan centang pernyataan sebelum melanjutkan.', 'INVALID_PAYLOAD');
  let report = detail.report, bundle = detail.active_bundle;
  const ids = items.map(item => item.id);
  if (!bundle || !sameEvidence(bundle.items, ids)) {
    const result = await request(`reports/${report.id}/bundles/`, {method: 'POST', key: crypto.randomUUID(),
      body: {evidence_ids: ids, expected_revision: report.revision}});
    const prepared = result.data;
    if (prepared?.report?.id !== report.id || prepared?.object?.report_id !== report.id ||
        !prepared.object.id || !sameEvidence(prepared.object.items || [], ids)) {
      throw new ApiError('Respons persiapan bukti belum dapat dipastikan. Periksa permintaan dan laporan tersimpan.', 'RESPONSE_UNKNOWN');
    }
    report = prepared.report; bundle = prepared.object;
    onPrepared({...detail, report, active_bundle: bundle, active_narrative: null, current_card: null});
  }
  return request(`reports/${report.id}/analyses/`, {method: 'POST', key: crypto.randomUUID(), body: {
    mode: 'EVIDENCE', bundle_id: bundle.id, input_revision: report.input_revision, expected_revision: report.revision,
  }});
}
