import hashlib,uuid
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import *

def extraction():
    return {'location_text':None,'time_text':None,'occurred_at':None,'involved_parties':[],
            'impacts':[],'victims':[],'affected_objects':[]}

def source_chain(owner,official=False):
    report=Report.objects.create(owner=owner)
    evidence=EvidenceItem.objects.create(report=report,type='TEXT',text_content='Air meluap ke jalan.',
        byte_size=23,sha256=hashlib.sha256(b'fixture').hexdigest(),uploaded_by=owner)
    with transaction.atomic():
        bundle=EvidenceBundle.objects.create(report=report,version_number=1,source_digest='a'*64,created_by=owner)
        EvidenceBundleItem.objects.create(bundle=bundle,evidence=evidence,position=1)
    ledger=IdempotencyRecord.objects.create(actor=owner,report=report,key=uuid.uuid4(),scope='test.analysis',request_hash='b'*64)
    run=AnalysisRun.objects.create(report=report,bundle=bundle,input_revision=1,request_record=ledger,
        mode='EVIDENCE',route='T',started_at=timezone.now(),execution_token=ledger.execution_token)
    narrative=NarrativeVersion.objects.create(report=report,bundle=bundle,producer_run=run,version_number=1,
        text='Air meluap ke jalan.',origin='NORMALIZER')
    sena=SENAResult.objects.create(analysis_run=run,narrative=narrative,category='FLOOD',confidence='.9',model_version='fixture-only')
    nara=NARAResult.objects.create(analysis_run=run,narrative=narrative,normalized_output=extraction(),model_version='fixture-only')
    card=IncidentCardVersion.objects.create(report=report,bundle=bundle,narrative=narrative,sena_result=sena,nara_result=nara,
        version_number=1,source_kind='AI_FUSION',data=dict(event_type='FLOOD',**extraction()),fusion_version='fixture-only')
    run.output_narrative=narrative;run.status='SUCCEEDED';run.finished_at=timezone.now();run.save()
    ledger.state='SUCCEEDED';ledger.finished_at=timezone.now();ledger.expires_at=timezone.now()+timedelta(days=1)
    ledger.response_status=201;ledger.response_payload={'data':{'fixture':True}};ledger.save()
    report.active_bundle=bundle;report.active_narrative=narrative;report.current_card_version=card
    report.preparation_status='AWAITING_CONFIRMATION'
    if official:
        HumanVerification.objects.create(report=report,card_version=card,reporter=owner,confirmed_at=timezone.now())
        report.official_card_version=card;report.submitted_at=timezone.now();report.preparation_status='READY';report.workflow_status='SUBMITTED'
    report.save()
    return report,bundle,run,card,evidence
