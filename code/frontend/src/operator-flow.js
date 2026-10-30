import {ApiError} from './api.js';

export function savedReview(detail, packet) {
  const context=packet.reviewContext;
  if(!context||detail?.report?.id!==packet.id||!detail.private_access)return null;
  return detail.reviews?.find(item=>!context.previousIds.includes(item.id)&&
    item.card_version_id===context.cardId&&item.operator_id===context.operatorId&&
    item.outcome===packet.body.outcome&&item.reason===packet.body.reason)||null;
}

export function canDraftPublication(detail) {
  const report=detail?.report,review=detail?.latest_review;
  return Boolean(report&&report.workflow_status!=='CLOSED'&&report.validation_status==='VALID'&&
    review?.outcome==='VALID'&&review.card_version_id===report.official_card_version_id&&
    detail.official_card?.id===report.official_card_version_id&&!detail.active_candidate&&
    ['NOT_DECIDED','INTERNAL','PENDING_APPROVAL','PUBLISHED'].includes(report.publication_status));
}

export function publicationValues(form) {
  const values=Object.fromEntries(['summary','general_location','time_text','occurred_at','general_impact','handling_update']
    .map(key=>[key,key==='summary'?String(form[key]??'').trim():String(form[key]??'').trim()||null]));
  if(!values.summary)throw new ApiError('Isi ringkasan publik sebelum melanjutkan.','INVALID_PAYLOAD');
  if(values.occurred_at){
    if(!/(Z|[+-]\d{2}:\d{2})$/i.test(values.occurred_at)||!Number.isFinite(Date.parse(values.occurred_at)))
      throw new ApiError('Isi waktu pasti beserta zona waktunya, atau kosongkan jika belum diketahui.','INVALID_PAYLOAD');
    values.occurred_at=new Date(values.occurred_at).toISOString();
  }
  return values;
}

export function publicationReceipt(response, packet) {
  const result=response?.data;
  if(result?.report?.id!==packet.reportId||!Number.isInteger(result.report.revision)||
    result.report.revision<=packet.body.expected_revision||
    (packet.versionId&&result.object?.id!==packet.versionId)||
    (packet.action==='create'&&(!result.object?.id||result.object.state!=='DRAFT')))
    throw new ApiError('Respons tindakan belum dapat dipastikan. Baca hasil tersimpan.','RESPONSE_UNKNOWN');
  return result;
}

export function publicationRequest(record, packet) {
  if(record?.key!==packet.key||record.report_id!==packet.reportId||record.scope!==packet.scope)
    throw new ApiError('Referensi tindakan publikasi tidak sesuai.','INVALID_RESPONSE');
  return record;
}

// The one-click confirmation may only approve the exact content just inspected.
export function reviewedPublicationCandidate(detail, versionId, values, category) {
  const version=detail?.active_candidate,contents=version?.data;
  const equal=(key)=>key==='occurred_at'&&values[key]&&contents?.[key]?
    Date.parse(values[key])===Date.parse(contents[key]):(values[key]??null)===(contents?.[key]??null);
  if(!version||version.id!==versionId||version.state!=='DRAFT'||
    version.card_version_id!==detail.report.official_card_version_id||contents?.event_type!==category||
    Object.keys(contents).length!==7||!Object.keys(values).every(equal))
    throw new ApiError('Isi versi tersimpan berbeda dari pratinjau yang Anda periksa. Periksa ulang sebelum mengonfirmasi.','VERSION_CONFLICT');
  return version;
}
