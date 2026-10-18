from uuid import uuid4
from django.db import connection
from common.api import ApiProblem
from .models import AuditEvent

ALLOWED_CHANGE_FIELDS = {
    'changed_fields','permission_ids','role','is_active','email_verified','challenge_id','purpose',
    'revision','input_revision','preparation_status','workflow_status','validation_status','publication_status',
    'card_version_id','bundle_id','assignment_id','operator_id','outcome','status','state','error_code',
    'result_id','result_type','run_id','published_version_id','candidate_id','reason_recorded',
}

def record_event(*, actor, action, object_type, object_id=None, report=None, before=None, after=None, request_id=None, acting_role=None):
    if not connection.in_atomic_block:
        raise RuntimeError('Audit mutasi harus berada dalam transaksi yang sama.')
    before,after=before or {},after or {}
    if (set(before)|set(after))-ALLOWED_CHANGE_FIELDS:
        raise ValueError('Audit hanya menerima whitelist metadata perubahan, tanpa isi/rahasia.')
    role=actor.role if actor else 'SYSTEM'
    if acting_role is not None and acting_role!=role:
        from .permissions import effective_permissions,is_assignee
        if not (actor and role=='ADMIN' and acting_role=='OPERATOR' and report
                and 'view_assigned_report' in effective_permissions(actor) and is_assignee(actor,report)):
            raise ValueError('Peran audit harus mencerminkan kewenangan yang benar-benar digunakan.')
        role=acting_role
    return AuditEvent.objects.create(actor=actor,actor_role=role,
        report=report,action=action,object_type=object_type,object_id=object_id,
        before=before,after=after,request_id=request_id or uuid4())

