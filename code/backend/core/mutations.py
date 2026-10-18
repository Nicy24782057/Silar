"""Shared short-transaction primitives. AI execution belongs to SLR_11."""
from dataclasses import dataclass
from datetime import timedelta
import hashlib,json,uuid
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from accounts.models import User
from common.api import ApiProblem
from .models import IdempotencyRecord,Report

@dataclass
class MutationResult:
    payload: dict
    status: int=200
    result_type: str|None=None
    result_id: uuid.UUID|None=None
    replayed: bool=False

def request_digest(payload):
    encoded=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False,cls=DjangoJSONEncoder).encode()
    return hashlib.sha256(encoded).hexdigest()

def _no_credentials(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k.lower() in {'password','password_confirm','access','refresh','code','code_digest','secret_key','api_key','authorization','cookie'}:
                raise ValueError('Ledger tidak menyimpan kredensial atau OTP.')
            _no_credentials(v)
    elif isinstance(value,list):
        for v in value:_no_credentials(v)

def atomic_mutation(*,actor,key,scope,payload,authorize,apply,report_id=None,expected_revision=None):
    """authorize(actor,report) runs BEFORE replay; apply returns MutationResult.

    apply must keep report revisions/audit/resource changes in this transaction.
    Do not run model inference or send email inside this short transaction.
    Account/password operations deliberately do not use this response ledger.
    """
    try:key=uuid.UUID(str(key))
    except (ValueError,TypeError):raise ApiProblem('INVALID_PAYLOAD','Idempotency-Key harus UUID.',400)
    if not isinstance(payload,dict):raise ApiProblem('INVALID_PAYLOAD','Payload harus objek JSON.',400)
    _no_credentials(payload)
    with transaction.atomic():
        fresh_actor=User.objects.select_for_update().get(pk=actor.pk)
        report=Report.objects.select_for_update().get(pk=report_id) if report_id else None
        authorize(fresh_actor,report)
        record=IdempotencyRecord.objects.select_for_update().filter(actor=fresh_actor,key=key).first()
        digest=request_digest(payload)
        if record:
            if record.scope!=scope or record.request_hash!=digest or record.report_id!=(report.id if report else None):
                raise ApiProblem('IDEMPOTENCY_MISMATCH','Key sudah digunakan untuk tindakan atau payload berbeda.',409)
            if record.state in ('RUNNING','UNKNOWN'):
                raise ApiProblem('REQUEST_'+record.state,'Hasil request sebelumnya belum terminal.',409)
            if not record.expires_at or record.expires_at<=timezone.now() or record.response_payload is None:
                raise ApiProblem('IDEMPOTENCY_EXPIRED','Masa replay habis. Baca keadaan tersimpan; key tidak dapat digunakan ulang.',409)
            return MutationResult(record.response_payload,record.response_status,record.result_type,record.result_id,True)
        if report and (not isinstance(expected_revision,int) or report.revision!=expected_revision):
            raise ApiProblem('REVISION_CONFLICT','Laporan berubah. Ambil detail terbaru.',409)
        record=IdempotencyRecord.objects.create(actor=fresh_actor,report=report,key=key,scope=scope,request_hash=digest)
        result=apply(fresh_actor,report)
        if not isinstance(result,MutationResult):raise TypeError('apply harus mengembalikan MutationResult.')
        _no_credentials(result.payload)
        record.state='SUCCEEDED';record.response_payload=json.loads(json.dumps(result.payload,cls=DjangoJSONEncoder))
        record.response_status=result.status;record.result_type=result.result_type;record.result_id=result.result_id
        record.finished_at=timezone.now();record.expires_at=record.finished_at+timedelta(seconds=settings.IDEMPOTENCY_TTL_SECONDS)
        record.save()
        return result

