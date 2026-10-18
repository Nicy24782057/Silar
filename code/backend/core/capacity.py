"""Database-backed reservation building blocks for the future SLR_11 pipeline.

No worker, queue, auto retry, AI inference, or recovery HTTP endpoint is created.
"""
from contextlib import contextmanager
from datetime import timedelta
import uuid
import psycopg
from django.conf import settings
from django.db import connection,transaction,IntegrityError
from django.utils import timezone
from common.api import ApiProblem
from .models import Report,AnalysisRun,IdempotencyRecord
from .permissions import require_owner_draft
from .mutations import request_digest,_no_credentials
from .audit import record_event

@contextmanager
def analysis_slot():
    config=settings.DATABASES['default']
    dedicated=psycopg.connect(dbname=config['NAME'],user=config['USER'],password=config.get('PASSWORD',''),
        host=config.get('HOST',''),port=config.get('PORT','5432'),autocommit=True,connect_timeout=8)
    acquired=None
    try:
        for slot in range(1,settings.ANALYSIS_CAPACITY+1):
            if AnalysisRun.objects.filter(capacity_slot=slot,status__in=['RUNNING','UNKNOWN']).exists():continue
            with dedicated.cursor() as cursor:
                cursor.execute('SELECT pg_try_advisory_lock(%s,%s)',(731008,slot))
                if cursor.fetchone()[0]:acquired=slot;break
        if acquired is None:raise ApiProblem('CAPACITY_BUSY','Kapasitas analisis sedang dipakai.',503)
        yield acquired
    finally:
        if acquired is not None:
            with dedicated.cursor() as cursor:cursor.execute('SELECT pg_advisory_unlock(%s,%s)',(731008,acquired))
        dedicated.close()

def create_reserved_run(*,actor,report_id,bundle_id,input_revision,expected_revision,key,mode,route,slot,narrative_id=None,execution_context=None):
    with transaction.atomic():
        report=Report.objects.select_for_update().get(pk=report_id)
        require_owner_draft(actor,report)
        if report.revision!=expected_revision:raise ApiProblem('REVISION_CONFLICT','Laporan berubah.',409)
        if report.input_revision!=input_revision or report.active_bundle_id!=bundle_id:
            raise ApiProblem('INPUT_CHANGED','Sumber analisis sudah berubah.',409)
        active=report.analysis_runs.filter(status__in=['RUNNING','UNKNOWN']).first()
        if active:raise ApiProblem('REQUEST_'+active.status,'Run sebelumnya belum terminal.',409)
        token=uuid.uuid4()
        payload={'bundle_id':str(bundle_id),'input_revision':input_revision,'expected_revision':expected_revision,'mode':mode}
        if narrative_id:payload['narrative_id']=str(narrative_id)
        try:
            with transaction.atomic():
                ledger=IdempotencyRecord.objects.create(actor=actor,report=report,key=key,
                    scope=f'POST reports/{report.id}/analyses/',request_hash=request_digest(payload),execution_token=token)
                run=AnalysisRun.objects.create(report=report,bundle_id=bundle_id,input_narrative_id=narrative_id,
                    input_revision=input_revision,request_record=ledger,mode=mode,route=route,capacity_slot=slot,
                    execution_token=token,execution_context=execution_context or {},started_at=timezone.now())
        except IntegrityError:raise ApiProblem('CAPACITY_BUSY','Slot atau key sudah dipakai; baca rekaman sebelumnya.',503)
        report.preparation_status='PROCESSING';report.current_card_version=None;report.revision+=1;report.save()
        record_event(actor=actor,action='ANALYSIS_RESERVED',object_type='AnalysisRun',object_id=run.id,report=report,
                     after={'run_id':str(run.id),'state':'RUNNING','revision':report.revision})
        return run

def fail_known_run(run_id,token,code='ANALYSIS_FAILED'):
    with transaction.atomic():
        # Lock order is Report -> AnalysisRun -> ledger across finalization/recovery.
        target=AnalysisRun.objects.get(pk=run_id)
        report=Report.objects.select_for_update().get(pk=target.report_id)
        run=AnalysisRun.objects.select_for_update().get(pk=run_id)
        ledger=IdempotencyRecord.objects.select_for_update().get(pk=run.request_record_id)
        if run.execution_token!=token or ledger.execution_token!=token or run.status not in ['RUNNING','UNKNOWN']:
            raise ApiProblem('TRANSITION_REJECTED','Eksekusi lama tidak dapat melakukan finalisasi.',422)
        if report.input_revision!=run.input_revision:code='INPUT_CHANGED'
        now=timezone.now();run.status='FAILED';run.finished_at=now;run.error_code=code;run.save()
        ledger.state='FAILED';ledger.error_code=code;ledger.finished_at=now
        ledger.expires_at=now+timedelta(seconds=settings.IDEMPOTENCY_TTL_SECONDS)
        ledger.response_status=409 if code=='INPUT_CHANGED' else 503
        ledger.response_payload={'error':{'code':code,'message':'Analisis belum berhasil. Baca keadaan tersimpan.', 'fields':{},'request_id':str(uuid.uuid4())}}
        ledger.save()
        if report.input_revision==run.input_revision:report.preparation_status='FAILED'
        report.revision+=1;report.save()
        record_event(actor=None,action='ANALYSIS_FAILED',object_type='AnalysisRun',object_id=run.id,report=report,
                     after={'state':'FAILED','error_code':code,'revision':report.revision})
        return run
