import hashlib,uuid
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import *

def extraction():
    return {'location_text':None,'time_text':None,'occurred_at':None,'involved_parties':[],
            'impacts':[],'victims':[],'affected_objects':[]}

def source_chain(owner,official=False,category='FLOOD',uncertain=False,channels='T'):
    if channels not in ['T','A','I','TA','TI','AI','TAI']:
        raise ValueError('Unknown fixture route')
    report=Report.objects.create(owner=owner)
    items=[]
    for channel in channels:
        values={'type':'TEXT','text_content':'Air meluap ke jalan.'} if channel=='T' else {
            'type':'AUDIO' if channel=='A' else 'IMAGE','file_key':'fixture-not-read/'+uuid.uuid4().hex,
            'original_name':'fixture.wav' if channel=='A' else 'fixture.png',
            'mime_type':'audio/wav' if channel=='A' else 'image/png'}
        items.append(EvidenceItem.objects.create(report=report,byte_size=23,
            sha256=hashlib.sha256(b'fixture').hexdigest(),uploaded_by=owner,**values))
    evidence=items[0]
    with transaction.atomic():
        bundle=EvidenceBundle.objects.create(report=report,version_number=1,source_digest='a'*64,created_by=owner)
        for position,item in enumerate(items,1):
            EvidenceBundleItem.objects.create(bundle=bundle,evidence=item,position=position)
    ledger=IdempotencyRecord.objects.create(actor=owner,report=report,key=uuid.uuid4(),scope='test.analysis',request_hash='b'*64)
    run=AnalysisRun.objects.create(report=report,bundle=bundle,input_revision=1,request_record=ledger,
        mode='EVIDENCE',route=channels,started_at=timezone.now(),execution_token=ledger.execution_token)
    narrative=NarrativeVersion.objects.create(report=report,bundle=bundle,producer_run=run,version_number=1,
        text='Air meluap ke jalan.',origin='NORMALIZER' if channels in ['T','A'] else 'GEMINI')
    sena=SENAResult.objects.create(analysis_run=run,narrative=narrative,category=category,confidence='.9',model_version='fixture-only')
    nara=NARAResult.objects.create(analysis_run=run,narrative=narrative,normalized_output=extraction(),model_version='fixture-only')
    card=IncidentCardVersion.objects.create(report=report,bundle=bundle,narrative=narrative,sena_result=sena,nara_result=nara,
        version_number=1,source_kind='AI_FUSION',data=dict(event_type=None if category=='NON_EVENT' else category,**extraction()),fusion_version='fixture-only',
        uncertain=uncertain,uncertain_reasons=['LOW_CLASSIFICATION_CONFIDENCE'] if uncertain else [])
    if 'A' in channels:
        run.used_transcript=Transcript.objects.create(report=report,evidence=next(item for item in items if item.type=='AUDIO'),
            analysis_run=run,text='Air meluap ke jalan.',model_version='fixture-whisper',duration_ms=1000)
    run.output_narrative=narrative;run.status='SUCCEEDED';run.stage='PERSIST';run.finished_at=timezone.now();run.save()
    ledger.state='SUCCEEDED';ledger.finished_at=timezone.now();ledger.expires_at=timezone.now()+timedelta(days=1)
    ledger.response_status=201;ledger.response_payload={'data':{'fixture':True}};ledger.save()
    report.active_bundle=bundle;report.active_narrative=narrative;report.current_card_version=card
    report.preparation_status='AWAITING_CONFIRMATION'
    if category=='NON_EVENT':
        report.preparation_status='BLOCKED';report.blocked_reason='NON_EVENT'
    if official:
        HumanVerification.objects.create(report=report,card_version=card,reporter=owner,confirmed_at=timezone.now())
        report.official_card_version=card;report.submitted_at=timezone.now();report.preparation_status='READY';report.workflow_status='SUBMITTED'
    report.save()
    return report,bundle,run,card,evidence
