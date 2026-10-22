export const fieldLabels = Object.freeze({location_text: 'Lokasi', time_text: 'Waktu yang disebut', occurred_at: 'Waktu pasti', involved_parties: 'Pihak terlibat', impacts: 'Dampak', victims: 'Informasi korban', affected_objects: 'Objek terdampak'});
const warningLabels = {INFORMATION_AS_IMPACT_SUGGESTION: 'Usulan dampak perlu diperiksa'};

export function analysisContext(detail) {
  const card = detail?.current_card, run = detail?.latest_run;
  const matches = Boolean(card && run?.status === 'SUCCEEDED' &&
    card.bundle_id && card.bundle_id === run.bundle_id &&
    card.nara_result_id && card.nara_result_id === run.nara?.id &&
    card.sena_result_id && card.sena_result_id === run.sena?.id &&
    card.narrative_id && card.narrative_id === run.nara?.narrative_id &&
    card.narrative_id === run.sena?.narrative_id &&
    run.nara.analysis_run_id === run.id && run.sena.analysis_run_id === run.id);
  const warnings = matches && Array.isArray(run.nara.normalization_warnings)
    ? run.nara.normalization_warnings.filter(item => item && typeof item.code === 'string').map(item => ({
        message: Object.hasOwn(warningLabels, item.code) ? warningLabels[item.code] : 'Informasi hasil ekstraksi perlu diperiksa',
        field: Object.hasOwn(fieldLabels, item.field) ? fieldLabels[item.field] : 'Informasi kejadian',
      })) : [];
  const candidates = [detail?.active_narrative, matches ? run.output_narrative : null];
  const narrative = card?.narrative_id ? candidates.find(item => item?.id === card.narrative_id) || null : null;
  return {matches, warnings, narrative, sena: matches ? run.sena : null,
    previous: Boolean(card && run && !matches)};
}
