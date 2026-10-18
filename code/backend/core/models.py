import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F
from .validators import json_object, json_array, nara_data, card_data, public_data, normalization_warnings, EVENTS

USER = settings.AUTH_USER_MODEL
PROTECT = models.PROTECT

class Stamped(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False, validate_constraints=False)
        return super().save(*args, **kwargs)

class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Rekaman immutable; buat versi baru.')

    def delete(self):
        raise ValidationError('Bukti, versi, dan audit tidak dihapus.')

class Immutable(Stamped):
    objects = ImmutableQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Rekaman immutable; buat versi baru.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Bukti, versi, dan audit tidak dihapus.')

class Preparation(models.TextChoices):
    DRAFT='DRAFT'; PROCESSING='PROCESSING'; AWAITING_CONFIRMATION='AWAITING_CONFIRMATION'; READY='READY'; BLOCKED='BLOCKED'; FAILED='FAILED'

class Workflow(models.TextChoices):
    NOT_SUBMITTED='NOT_SUBMITTED'; SUBMITTED='SUBMITTED'; ASSIGNED='ASSIGNED'; IN_REVIEW='IN_REVIEW'; FOLLOW_UP='FOLLOW_UP'; CLOSED='CLOSED'

class Validation(models.TextChoices):
    NOT_REVIEWED='NOT_REVIEWED'; VALID='VALID'; INVALID='INVALID'; INCONCLUSIVE='INCONCLUSIVE'

class Publication(models.TextChoices):
    NOT_DECIDED='NOT_DECIDED'; INTERNAL='INTERNAL'; PENDING_APPROVAL='PENDING_APPROVAL'; APPROVED='APPROVED'; PUBLISHED='PUBLISHED'

class ExecutionState(models.TextChoices):
    RUNNING='RUNNING'; SUCCEEDED='SUCCEEDED'; FAILED='FAILED'; UNKNOWN='UNKNOWN'

class Report(Stamped):
    owner = models.ForeignKey(USER, on_delete=PROTECT, related_name='owned_reports')
    revision = models.PositiveIntegerField(default=1)
    input_revision = models.PositiveIntegerField(default=1)
    preparation_status = models.CharField(max_length=30, choices=Preparation.choices, default=Preparation.DRAFT)
    workflow_status = models.CharField(max_length=25, choices=Workflow.choices, default=Workflow.NOT_SUBMITTED)
    validation_status = models.CharField(max_length=20, choices=Validation.choices, default=Validation.NOT_REVIEWED)
    publication_status = models.CharField(max_length=25, choices=Publication.choices, default=Publication.NOT_DECIDED)
    active_bundle = models.ForeignKey('EvidenceBundle', null=True, blank=True, on_delete=PROTECT, related_name='+')
    active_narrative = models.ForeignKey('NarrativeVersion', null=True, blank=True, on_delete=PROTECT, related_name='+')
    current_card_version = models.ForeignKey('IncidentCardVersion', null=True, blank=True, on_delete=PROTECT, related_name='+')
    official_card_version = models.ForeignKey('IncidentCardVersion', null=True, blank=True, on_delete=PROTECT, related_name='+')
    latest_review = models.ForeignKey('OperatorReview', null=True, blank=True, on_delete=PROTECT, related_name='+')
    active_publication_candidate = models.ForeignKey('PublicationVersion', null=True, blank=True, on_delete=PROTECT, related_name='+')
    published_version = models.ForeignKey('PublicationVersion', null=True, blank=True, on_delete=PROTECT, related_name='+')
    blocked_reason = models.CharField(max_length=30, null=True, blank=True)
    publication_decision_reason = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(USER, null=True, blank=True, on_delete=PROTECT, related_name='+', db_column='closed_by')
    closure_note = models.TextField(null=True, blank=True)

    class Meta:
        permissions = [
            ('view_queue','Melihat antrean'), ('view_assigned_report','Membaca laporan tugas'),
            ('claim_report','Mengambil laporan'), ('review_report','Mencatat pemeriksaan'),
            ('manage_followup','Mengelola tindak lanjut'), ('publish_report','Mengelola publikasi'),
            ('close_report','Menutup laporan'), ('manage_operator','Mengelola akun Operator'),
            ('assign_report','Menugaskan laporan'), ('monitor_report','Monitoring laporan'),
            ('view_private_evidence','Membaca sumber privat laporan resmi'),
            ('view_audit','Membaca audit'), ('monitor_services','Monitoring layanan'),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(revision__gte=1, input_revision__gte=1), name='report_revisions_positive'),
            models.CheckConstraint(condition=Q(preparation_status__in=Preparation.values), name='report_preparation_allowed'),
            models.CheckConstraint(condition=Q(workflow_status__in=Workflow.values), name='report_workflow_allowed'),
            models.CheckConstraint(condition=Q(validation_status__in=Validation.values), name='report_validation_allowed'),
            models.CheckConstraint(condition=Q(publication_status__in=Publication.values), name='report_publication_allowed'),
            models.CheckConstraint(condition=Q(submitted_at__isnull=True)|Q(official_card_version__isnull=False), name='submitted_requires_official_version'),
            models.CheckConstraint(condition=~Q(workflow_status='CLOSED')|Q(closed_at__isnull=False, closed_by__isnull=False, closure_note__isnull=False)&~Q(closure_note=''), name='closed_requires_metadata'),
            models.CheckConstraint(condition=Q(blocked_reason__isnull=True)|Q(blocked_reason='NON_EVENT',preparation_status='BLOCKED'), name='blocked_reason_consistent'),
        ]
        indexes = [models.Index(fields=['owner','-created_at']), models.Index(fields=['workflow_status','submitted_at'])]

    def clean(self):
        for field in ['active_bundle','active_narrative','current_card_version','official_card_version','latest_review','active_publication_candidate','published_version']:
            obj = getattr(self, field) if getattr(self, field+'_id') else None
            if obj is not None and obj.report_id != self.id:
                raise ValidationError({field: 'Sumber harus milik Report yang sama.'})

class EvidenceItem(Immutable):
    report = models.ForeignKey(Report, on_delete=PROTECT, related_name='evidence')
    type = models.CharField(max_length=5, choices=[(x,x) for x in ['TEXT','AUDIO','IMAGE']])
    text_content = models.TextField(null=True, blank=True)
    file_key = models.CharField(max_length=512, null=True, blank=True)
    original_name = models.CharField(max_length=255, null=True, blank=True)
    mime_type = models.CharField(max_length=127, null=True, blank=True)
    byte_size = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(USER, on_delete=PROTECT, related_name='+', db_column='uploaded_by')
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(type='TEXT',text_content__isnull=False,file_key__isnull=True)&~Q(text_content='')|Q(type__in=['AUDIO','IMAGE'],text_content__isnull=True,file_key__isnull=False)&~Q(file_key=''), name='evidence_channel_content')]
    def clean(self):
        if self.uploaded_by_id != self.report.owner_id:
            raise ValidationError('Bukti hanya disimpan oleh pemilik laporan.')
        if self.type=='TEXT' and not (self.text_content or '').strip():
            raise ValidationError('Teks bukti tidak boleh kosong.')

class EvidenceBundle(Immutable):
    report = models.ForeignKey(Report, on_delete=PROTECT, related_name='bundles')
    version_number = models.PositiveIntegerField()
    source_digest = models.CharField(max_length=64)
    created_by = models.ForeignKey(USER, on_delete=PROTECT, related_name='+', db_column='created_by')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['report','version_number'],name='bundle_version_unique'),models.CheckConstraint(condition=Q(version_number__gte=1),name='bundle_version_positive')]

class EvidenceBundleItem(Immutable):
    bundle = models.ForeignKey(EvidenceBundle, on_delete=PROTECT, related_name='items')
    evidence = models.ForeignKey(EvidenceItem, on_delete=PROTECT)
    position = models.PositiveIntegerField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['bundle','evidence'],name='bundle_evidence_unique'),models.UniqueConstraint(fields=['bundle','position'],name='bundle_position_unique'),models.CheckConstraint(condition=Q(position__gte=1),name='bundle_position_positive')]
    def clean(self):
        if self.bundle.report_id != self.evidence.report_id:
            raise ValidationError('Bundle dan bukti harus dari Report yang sama.')

class NarrativeVersion(Immutable):
    report = models.ForeignKey(Report,on_delete=PROTECT,related_name='narratives')
    bundle = models.ForeignKey(EvidenceBundle,on_delete=PROTECT)
    parent = models.ForeignKey('self',null=True,blank=True,on_delete=PROTECT)
    producer_run = models.ForeignKey('AnalysisRun',null=True,blank=True,on_delete=PROTECT,related_name='+')
    version_number = models.PositiveIntegerField()
    text = models.TextField()
    origin = models.CharField(max_length=25,choices=[(x,x) for x in ['NORMALIZER','GEMINI','REPORTER_REVISION']])
    created_by = models.ForeignKey(USER,null=True,blank=True,on_delete=PROTECT,db_column='created_by')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['report','version_number'],name='narrative_version_unique'),models.UniqueConstraint(fields=['producer_run'],condition=Q(producer_run__isnull=False),name='narrative_producer_unique'),models.CheckConstraint(condition=Q(version_number__gte=1),name='narrative_version_positive'),models.CheckConstraint(condition=Q(origin__in=['NORMALIZER','GEMINI','REPORTER_REVISION']),name='narrative_origin_allowed')]
    def clean(self):
        same_report(self,['bundle','parent','producer_run'])
        if not self.text.strip():raise ValidationError('Narasi tidak boleh kosong.')
        if self.origin=='REPORTER_REVISION' and (self.created_by_id!=self.report.owner_id or self.producer_run_id):
            raise ValidationError('Revisi narasi harus berasal dari Reporter pemilik.')

class AnalysisRun(Stamped):
    report = models.ForeignKey(Report,on_delete=PROTECT,related_name='analysis_runs')
    bundle = models.ForeignKey(EvidenceBundle,on_delete=PROTECT)
    input_narrative = models.ForeignKey(NarrativeVersion,null=True,blank=True,on_delete=PROTECT,related_name='+')
    output_narrative = models.ForeignKey(NarrativeVersion,null=True,blank=True,on_delete=PROTECT,related_name='+')
    used_transcript = models.ForeignKey('Transcript',null=True,blank=True,on_delete=PROTECT,related_name='+')
    input_revision = models.PositiveIntegerField()
    request_record = models.OneToOneField('IdempotencyRecord',on_delete=PROTECT)
    mode = models.CharField(max_length=25,choices=[('EVIDENCE','EVIDENCE'),('NARRATIVE_REVISION','NARRATIVE_REVISION')])
    route = models.CharField(max_length=40,choices=[(x,x) for x in ['T','A','I','TA','TI','AI','TAI']])
    status = models.CharField(max_length=15,choices=ExecutionState.choices,default=ExecutionState.RUNNING)
    stage = models.CharField(max_length=15,choices=[(x,x) for x in ['INPUT','WHISPER','NARRATIVE','SENA','NARA','FUSION','PERSIST']],default='INPUT')
    execution_token = models.UUIDField(default=uuid.uuid4)
    execution_context = models.JSONField(default=dict,validators=[json_object],blank=True)
    capacity_slot = models.PositiveIntegerField(default=1)
    model_versions = models.JSONField(default=dict,validators=[json_object],blank=True)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True,blank=True)
    error_code = models.CharField(max_length=80,null=True,blank=True)
    timings_ms = models.JSONField(default=dict,validators=[json_object],blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['report'],condition=Q(status__in=['RUNNING','UNKNOWN']),name='analysis_one_active_per_report'),
            models.UniqueConstraint(fields=['capacity_slot'],condition=Q(status__in=['RUNNING','UNKNOWN']),name='analysis_one_active_per_slot'),
            models.CheckConstraint(condition=Q(capacity_slot__gte=1,input_revision__gte=1),name='analysis_slot_revision_positive'),
            models.CheckConstraint(condition=Q(status__in=ExecutionState.values),name='analysis_state_allowed'),
            models.CheckConstraint(condition=Q(route__in=['T','A','I','TA','TI','AI','TAI']),name='analysis_route_allowed'),
            models.CheckConstraint(condition=Q(stage__in=['INPUT','WHISPER','NARRATIVE','SENA','NARA','FUSION','PERSIST']),name='analysis_stage_allowed'),
            models.CheckConstraint(condition=Q(mode='EVIDENCE',input_narrative__isnull=True)|Q(mode='NARRATIVE_REVISION',input_narrative__isnull=False),name='analysis_mode_input_consistent'),
            models.CheckConstraint(condition=Q(status__in=['RUNNING','UNKNOWN'],finished_at__isnull=True)|Q(status__in=['SUCCEEDED','FAILED'],finished_at__isnull=False),name='analysis_terminal_timestamp'),
        ]
    def clean(self):
        same_report(self,['bundle','input_narrative','output_narrative','used_transcript','request_record'])
        if self.capacity_slot>settings.ANALYSIS_CAPACITY:raise ValidationError('Slot melebihi konfigurasi kapasitas.')

class Transcript(Immutable):
    report = models.ForeignKey(Report,on_delete=PROTECT)
    evidence = models.ForeignKey(EvidenceItem,on_delete=PROTECT)
    analysis_run = models.ForeignKey(AnalysisRun,on_delete=PROTECT)
    text = models.TextField()
    model_version = models.CharField(max_length=100)
    duration_ms = models.PositiveBigIntegerField(null=True,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['analysis_run','evidence'],name='transcript_run_evidence_unique')]
    def clean(self):
        same_report(self,['evidence','analysis_run'])
        if self.evidence.type!='AUDIO':raise ValidationError('Transkrip harus menunjuk bukti audio.')

class SENAResult(Immutable):
    analysis_run = models.OneToOneField(AnalysisRun,on_delete=PROTECT,related_name='sena_result')
    narrative = models.ForeignKey(NarrativeVersion,on_delete=PROTECT)
    category = models.CharField(max_length=20,choices=[(x,x) for x in EVENTS+['NON_EVENT']])
    confidence = models.DecimalField(max_digits=6,decimal_places=5)
    raw_output = models.JSONField(default=dict,validators=[json_object],blank=True)
    model_version = models.CharField(max_length=100)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(confidence__gte=0,confidence__lte=1),name='sena_confidence_range'),models.CheckConstraint(condition=Q(category__in=EVENTS+['NON_EVENT']),name='sena_category_allowed')]
    def clean(self):
        if self.analysis_run.report_id!=self.narrative.report_id:raise ValidationError('Narasi hasil SENA harus sesuai run.')

class NARAResult(Immutable):
    analysis_run = models.OneToOneField(AnalysisRun,on_delete=PROTECT,related_name='nara_result')
    narrative = models.ForeignKey(NarrativeVersion,on_delete=PROTECT)
    raw_output = models.JSONField(default=dict,validators=[json_object],blank=True)
    normalized_output = models.JSONField(validators=[nara_data])
    normalization_warnings = models.JSONField(default=list,validators=[normalization_warnings],blank=True)
    model_version = models.CharField(max_length=100)
    def clean(self):
        if self.analysis_run.report_id!=self.narrative.report_id:raise ValidationError('Narasi hasil NARA harus sesuai run.')

class IncidentCardVersion(Immutable):
    report = models.ForeignKey(Report,on_delete=PROTECT,related_name='card_versions')
    bundle = models.ForeignKey(EvidenceBundle,on_delete=PROTECT)
    narrative = models.ForeignKey(NarrativeVersion,on_delete=PROTECT)
    sena_result = models.ForeignKey(SENAResult,on_delete=PROTECT)
    nara_result = models.ForeignKey(NARAResult,on_delete=PROTECT)
    parent = models.ForeignKey('self',null=True,blank=True,on_delete=PROTECT)
    version_number = models.PositiveIntegerField()
    source_kind = models.CharField(max_length=30,choices=[('AI_FUSION','AI_FUSION'),('REPORTER_FIELD_REVISION','REPORTER_FIELD_REVISION')])
    data = models.JSONField(validators=[card_data])
    uncertain = models.BooleanField(default=False)
    uncertain_reasons = models.JSONField(default=list,validators=[json_array],blank=True)
    fusion_version = models.CharField(max_length=100)
    created_by = models.ForeignKey(USER,null=True,blank=True,on_delete=PROTECT,db_column='created_by')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['report','version_number'],name='card_version_unique'),models.CheckConstraint(condition=Q(version_number__gte=1),name='card_version_positive'),models.CheckConstraint(condition=Q(source_kind__in=['AI_FUSION','REPORTER_FIELD_REVISION']),name='card_source_kind_allowed')]
    def clean(self):
        same_report(self,['bundle','narrative','parent'])
        if self.sena_result.narrative_id!=self.narrative_id or self.nara_result.narrative_id!=self.narrative_id:
            raise ValidationError('Kartu harus menggunakan narasi yang sama dengan SENA dan NARA.')
        if self.sena_result.analysis_run_id!=self.nara_result.analysis_run_id:
            raise ValidationError('SENA dan NARA pada satu kartu harus berasal dari run yang sama.')
        category=self.sena_result.category
        if self.data.get('event_type')!=(None if category=='NON_EVENT' else category):raise ValidationError('Kategori kartu mengikuti SENA.')
        if any(x not in ['LOW_CLASSIFICATION_CONFIDENCE','EXTRACTION_AMBIGUITY'] for x in self.uncertain_reasons) or bool(self.uncertain_reasons)!=self.uncertain:
            raise ValidationError('Penanda uncertain dan alasan harus konsisten.')
        if self.source_kind=='REPORTER_FIELD_REVISION':
            if not self.parent_id or self.created_by_id!=self.report.owner_id:raise ValidationError('Revisi field memerlukan parent dan Reporter pemilik.')
            for name in ['bundle_id','narrative_id','sena_result_id','nara_result_id','uncertain','uncertain_reasons']:
                if getattr(self,name)!=getattr(self.parent,name):raise ValidationError('Revisi field mempertahankan sumber serta flag parent.')

class HumanVerification(Immutable):
    report = models.ForeignKey(Report,on_delete=PROTECT)
    card_version = models.OneToOneField(IncidentCardVersion,on_delete=PROTECT)
    reporter = models.ForeignKey(USER,on_delete=PROTECT)
    confirmed_at = models.DateTimeField()
    def clean(self):
        same_report(self,['card_version'])
        if self.reporter_id!=self.report.owner_id:raise ValidationError('Konfirmasi hanya oleh Reporter pemilik.')
        if self.card_version.sena_result.category=='NON_EVENT':raise ValidationError('NON_EVENT belum dapat dikonfirmasi.')

class OperatorAssignment(Stamped):
    report = models.ForeignKey(Report,on_delete=PROTECT,related_name='assignments')
    operator = models.ForeignKey(USER,on_delete=PROTECT,related_name='report_assignments')
    assigned_by = models.ForeignKey(USER,on_delete=PROTECT,related_name='+',db_column='assigned_by')
    source = models.CharField(max_length=25,choices=[(x,x) for x in ['SELF_CLAIM','ADMIN_ASSIGNMENT','ADMIN_REASSIGNMENT']])
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True,blank=True)
    reason = models.TextField(null=True,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['report'],condition=Q(ended_at__isnull=True),name='one_current_assignment'),models.CheckConstraint(condition=Q(ended_at__isnull=True)|Q(ended_at__gte=F('started_at')),name='assignment_end_after_start'),models.CheckConstraint(condition=Q(source__in=['SELF_CLAIM','ADMIN_ASSIGNMENT','ADMIN_REASSIGNMENT']),name='assignment_source_allowed')]
        indexes = [models.Index(fields=['operator','ended_at'])]

class OperatorReview(Immutable):
    report = models.ForeignKey(Report,on_delete=PROTECT,related_name='reviews')
    card_version = models.ForeignKey(IncidentCardVersion,on_delete=PROTECT)
    assignment = models.ForeignKey(OperatorAssignment,on_delete=PROTECT)
    operator = models.ForeignKey(USER,on_delete=PROTECT)
    outcome = models.CharField(max_length=15,choices=[(x,x) for x in ['VALID','INVALID','INCONCLUSIVE']])
    reason = models.TextField()
    reviewed_at = models.DateTimeField()
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(outcome__in=['VALID','INVALID','INCONCLUSIVE']),name='review_outcome_allowed')]
    def clean(self):
        same_report(self,['card_version','assignment'])
        if not self.reason.strip() or self.card_version_id!=self.report.official_card_version_id:raise ValidationError('Review memerlukan versi resmi dan alasan.')

class FollowUpRecord(Stamped):
    report = models.ForeignKey(Report,on_delete=PROTECT,related_name='followups')
    assignment = models.ForeignKey(OperatorAssignment,on_delete=PROTECT)
    operator = models.ForeignKey(USER,on_delete=PROTECT)
    description = models.TextField()
    status = models.CharField(max_length=12,choices=[(x,x) for x in ['PENDING','DONE','CANCELLED']],default='PENDING')
    finished_at = models.DateTimeField(null=True,blank=True)
    completion_reason = models.TextField(null=True,blank=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(status='PENDING',finished_at__isnull=True)|Q(status__in=['DONE','CANCELLED'],finished_at__isnull=False),name='followup_terminal_metadata'),models.CheckConstraint(condition=~Q(status='CANCELLED')|Q(completion_reason__isnull=False)&~Q(completion_reason=''),name='cancelled_followup_reason')]
    def clean(self):same_report(self,['assignment'])

class PublicationVersion(Stamped):
    report = models.ForeignKey(Report,on_delete=PROTECT,related_name='publication_versions')
    card_version = models.ForeignKey(IncidentCardVersion,on_delete=PROTECT)
    parent = models.ForeignKey('self',null=True,blank=True,on_delete=PROTECT)
    version_number = models.PositiveIntegerField()
    data = models.JSONField(validators=[public_data])
    state = models.CharField(max_length=12,choices=[(x,x) for x in ['DRAFT','APPROVED','PUBLISHED','CANCELLED']],default='DRAFT')
    sanitized_by = models.ForeignKey(USER,on_delete=PROTECT,related_name='+',db_column='sanitized_by')
    approved_by = models.ForeignKey(USER,null=True,blank=True,on_delete=PROTECT,related_name='+',db_column='approved_by')
    approved_at = models.DateTimeField(null=True,blank=True)
    published_by = models.ForeignKey(USER,null=True,blank=True,on_delete=PROTECT,related_name='+',db_column='published_by')
    published_at = models.DateTimeField(null=True,blank=True)
    cancelled_at = models.DateTimeField(null=True,blank=True)
    cancelled_by = models.ForeignKey(USER,null=True,blank=True,on_delete=PROTECT,related_name='+',db_column='cancelled_by')
    cancellation_reason = models.TextField(null=True,blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['report','version_number'],name='publication_version_unique'),
            models.CheckConstraint(condition=Q(version_number__gte=1),name='publication_version_positive'),
            models.CheckConstraint(condition=Q(state__in=['DRAFT','APPROVED','PUBLISHED','CANCELLED']),name='publication_state_allowed'),
            models.CheckConstraint(condition=~Q(state__in=['APPROVED','PUBLISHED'])|Q(approved_by__isnull=False,approved_at__isnull=False),name='publication_approval_metadata'),
            models.CheckConstraint(condition=~Q(state='PUBLISHED')|Q(published_by__isnull=False,published_at__isnull=False),name='publication_publish_metadata'),
            models.CheckConstraint(condition=Q(state='CANCELLED',cancelled_at__isnull=False,cancelled_by__isnull=False,cancellation_reason__isnull=False)&~Q(cancellation_reason='')|~Q(state='CANCELLED')&Q(cancelled_at__isnull=True,cancelled_by__isnull=True,cancellation_reason__isnull=True),name='publication_cancel_metadata'),
        ]
        indexes = [models.Index(fields=['-published_at'])]
    def clean(self):
        same_report(self,['card_version','parent'])
        if self.card_version_id!=self.report.official_card_version_id:raise ValidationError('Publikasi harus dari versi resmi.')

class Notification(Stamped):
    recipient = models.ForeignKey(USER,on_delete=PROTECT)
    report = models.ForeignKey(Report,null=True,blank=True,on_delete=PROTECT)
    kind = models.CharField(max_length=80)
    message = models.CharField(max_length=300)
    read_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        indexes = [models.Index(fields=['recipient','read_at','-created_at'])]

class AuditEvent(Immutable):
    actor = models.ForeignKey(USER,null=True,blank=True,on_delete=PROTECT)
    actor_role = models.CharField(max_length=40)
    report = models.ForeignKey(Report,null=True,blank=True,on_delete=PROTECT)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=80)
    object_id = models.UUIDField(null=True,blank=True)
    before = models.JSONField(default=dict,validators=[json_object],blank=True)
    after = models.JSONField(default=dict,validators=[json_object],blank=True)
    request_id = models.UUIDField(default=uuid.uuid4)
    class Meta:
        indexes = [models.Index(fields=['report','created_at']),models.Index(fields=['actor','created_at'])]

class IdempotencyRecord(Stamped):
    actor = models.ForeignKey(USER,on_delete=PROTECT)
    report = models.ForeignKey(Report,null=True,blank=True,on_delete=PROTECT)
    key = models.UUIDField()
    scope = models.CharField(max_length=150)
    request_hash = models.CharField(max_length=64)
    state = models.CharField(max_length=15,choices=ExecutionState.choices,default=ExecutionState.RUNNING)
    result_type = models.CharField(max_length=80,null=True,blank=True)
    result_id = models.UUIDField(null=True,blank=True)
    execution_token = models.UUIDField(default=uuid.uuid4)
    response_status = models.PositiveIntegerField(null=True,blank=True)
    response_payload = models.JSONField(null=True,blank=True,validators=[json_object])
    error_code = models.CharField(max_length=80,null=True,blank=True)
    finished_at = models.DateTimeField(null=True,blank=True)
    expires_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['actor','key'],name='idempotency_actor_key_unique'),models.CheckConstraint(condition=Q(state__in=ExecutionState.values),name='idempotency_state_allowed')]
        indexes = [models.Index(fields=['actor','-created_at']),models.Index(fields=['state'])]

def same_report(instance, fields):
    report_id = instance.report_id
    for name in fields:
        if not getattr(instance,name+'_id'):
            continue
        obj = getattr(instance,name)
        if obj.report_id != report_id:
            raise ValidationError({name: 'Sumber harus berasal dari Report yang sama.'})
