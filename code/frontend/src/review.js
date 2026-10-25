import { ApiError } from './api.js';
import { analysisContext, fieldLabels } from './analysis.js';
import { textLength } from './domain.js';

export function reviewState(detail) {
  const report = detail?.report, card = detail?.current_card, run = detail?.latest_run;
  const context = analysisContext(detail);
  const held = ['RUNNING', 'UNKNOWN'].includes(run?.status);
  const submitted = Boolean(report?.submitted_at || report?.workflow_status !== 'NOT_SUBMITTED');
  const current = Boolean(context.matches && !held && card?.id === report?.current_card_version_id &&
    ['AWAITING_CONFIRMATION','READY','BLOCKED'].includes(report?.preparation_status) &&
    card?.bundle_id === report?.active_bundle_id && card?.narrative_id === report?.active_narrative_id &&
    run?.input_revision === report?.input_revision && run?.output_narrative_id === card?.narrative_id);
  const nonEvent = context.sena?.category === 'NON_EVENT' || (card && card.data?.event_type === null);
  const confirmed = Boolean(current && detail?.verification?.card_version_id === card.id);
  return {held, submitted, current, nonEvent, confirmed,
    canConfirm: Boolean(current && !nonEvent && !submitted && !confirmed),
    canSubmit: Boolean(current && !nonEvent && !submitted && confirmed && report?.preparation_status === 'READY')};
}

function localTimestamp(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const two = number => String(number).padStart(2, '0');
  return `${date.getFullYear()}-${two(date.getMonth()+1)}-${two(date.getDate())}T${two(date.getHours())}:${two(date.getMinutes())}:${two(date.getSeconds())}`;
}

export function cardForm(data) {
  return Object.fromEntries(Object.keys(fieldLabels).map(key => [key, key === 'occurred_at' ? localTimestamp(data?.[key]) :
    Array.isArray(data?.[key]) ? data[key].join('\n') : data?.[key] || '']));
}

export function correctionPatch(values, original) {
  const patch = {};
  for (const key of Object.keys(fieldLabels)) {
    if (values[key] === original[key]) continue;
    const text = values[key].trim();
    if (key === 'occurred_at') {
      if (!text) { patch[key] = null; continue; }
      const value = new Date(text);
      if (Number.isNaN(value.getTime())) throw new ApiError('Waktu pasti belum dapat dibaca.', 'INVALID_PAYLOAD');
      patch[key] = value.toISOString();
    } else if (key === 'location_text' || key === 'time_text') {
      const limit = key === 'location_text' ? 500 : 300;
      if (textLength(text) > limit) throw new ApiError(`${fieldLabels[key]} maksimal ${limit} karakter.`, 'INVALID_PAYLOAD');
      patch[key] = text || null;
    } else {
      const list = text ? text.split(/\r?\n/).map(value => value.trim()).filter(Boolean) : [];
      if (list.length > 100 || list.some(value => textLength(value) > 500))
        throw new ApiError(`${fieldLabels[key]} maksimal 100 baris, masing-masing 500 karakter.`, 'INVALID_PAYLOAD');
      patch[key] = list;
    }
  }
  return patch;
}
