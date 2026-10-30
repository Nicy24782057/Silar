from django.contrib.auth.models import Permission
from django.db.models import Q
from django.http import Http404
from common.api import ApiProblem
from accounts.models import Role

OPERATOR_PERMISSIONS = ('view_queue','view_assigned_report','claim_report','review_report','manage_followup','publish_report','close_report')
ADMIN_PERMISSIONS = ('manage_operator','assign_report','monitor_report','view_private_evidence','view_audit','monitor_services')
ALL_PERMISSIONS = OPERATOR_PERMISSIONS + ADMIN_PERMISSIONS

def permission_queryset():
    return Permission.objects.filter(content_type__app_label='core',content_type__model='report',codename__in=ALL_PERMISSIONS)

def effective_permissions(user):
    if not user or not user.is_active or not user.email_verified_at:
        return set()
    # Deliberately read explicit grants, not has_perm's superuser shortcut or a
    # stale _perm_cache. ADMIN alone never grants Operator decisions.
    return set(permission_queryset().filter(Q(user=user)|Q(group__user=user)).values_list('codename',flat=True).distinct())

def require_admin(user, permission):
    if not user or user.role!=Role.ADMIN or permission not in effective_permissions(user):
        raise ApiProblem('PERMISSION_DENIED','Tindakan memerlukan izin Admin yang sesuai.',403)

def require_operator(user, permission):
    if not user or user.role not in (Role.OPERATOR,Role.ADMIN) or not {'view_assigned_report',permission}<=effective_permissions(user):
        raise ApiProblem('PERMISSION_DENIED','Tindakan memerlukan izin Operator yang sesuai.',403)

def is_assignee(user, report):
    return report.assignments.filter(operator_id=user.id,ended_at__isnull=True).exists()

def can_read_report(user, report, content=False):
    if report.deleted_at is not None:
        return False
    if not user or not user.is_active or not user.email_verified_at:
        return False
    if user.role==Role.REPORTER:
        return report.owner_id==user.id
    if not report.submitted_at:
        return False
    permissions=effective_permissions(user)
    if user.role in (Role.OPERATOR,Role.ADMIN) and 'view_assigned_report' in permissions and is_assignee(user,report):
        return True
    if user.role==Role.ADMIN and 'monitor_report' in permissions:
        return not content or 'view_private_evidence' in permissions
    return False

def require_report_read(user, report, content=False):
    if not can_read_report(user,report,content):
        raise Http404

def require_owner_draft(user, report):
    require_report_read(user,report,True)
    if user.role!=Role.REPORTER or report.owner_id!=user.id:
        raise Http404
    if report.submitted_at:
        raise ApiProblem('TRANSITION_REJECTED','Versi resmi sudah dikunci.',422)

def require_handler(user, report, permission):
    require_operator(user,permission)
    require_report_read(user,report,True)
    if not is_assignee(user,report):raise Http404
    if report.workflow_status=='CLOSED':
        raise ApiProblem('TRANSITION_REJECTED','Penanganan laporan sudah ditutup.',422)

