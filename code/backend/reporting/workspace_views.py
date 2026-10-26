from datetime import timedelta
from time import perf_counter
from django.conf import settings
from django.db import connection
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import User
from common.api import ApiProblem, StrictSerializer, SilarPagination, validate_query, reject_query
from core.models import Report, OperatorAssignment, AuditEvent, AnalysisRun, Notification
from core.permissions import effective_permissions, require_admin, is_assignee
from . import workspace_services as services
from .serializers import fields, primitive, snapshot, bundle_data, card_data, narrative_data
from .views import response_mutation


class Revision(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=1)


class Assignment(Revision):
    operator_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=1500, trim_whitespace=True)


class Review(Revision):
    outcome = serializers.ChoiceField(choices=['VALID', 'INVALID', 'INCONCLUSIVE'])
    reason = serializers.CharField(max_length=3000, trim_whitespace=True)


class Followup(Revision):
    description = serializers.CharField(max_length=3000, trim_whitespace=True)


class FinishFollowup(Revision):
    status = serializers.ChoiceField(choices=['DONE', 'CANCELLED'])
    completion_reason = serializers.CharField(max_length=3000, trim_whitespace=True)


class Decision(Revision):
    decision = serializers.ChoiceField(choices=['INTERNAL', 'PREPARE'])
    reason = serializers.CharField(max_length=3000, trim_whitespace=True)


class Closure(Revision):
    closure_note = serializers.CharField(max_length=3000, trim_whitespace=True)


def allowed(user, permission):
    services.staff(user)
    if permission not in effective_permissions(user):
        raise ApiProblem('PERMISSION_DENIED', 'Anda belum memiliki izin untuk membuka halaman ini.', 403)


def reports_query(user, scope):
    services.staff(user)
    active = OperatorAssignment.objects.filter(report_id=OuterRef('pk'), ended_at__isnull=True)
    qs = Report.objects.filter(submitted_at__isnull=False).select_related('official_card_version', 'latest_review')
    if scope == 'queue':
        allowed(user, 'view_queue')
        qs = qs.filter(workflow_status='SUBMITTED').annotate(has_assignment=Exists(active)).filter(has_assignment=False)
    elif scope == 'assigned':
        allowed(user, 'view_assigned_report')
        qs = qs.filter(assignments__operator=user, assignments__ended_at__isnull=True)
    elif scope == 'monitor':
        require_admin(user, 'monitor_report')
    elif scope == 'assignment':
        require_admin(user, 'assign_report')
    else:
        raise ApiProblem('INVALID_PAYLOAD', 'Jenis daftar laporan tidak dikenal.', 400)
    return qs.prefetch_related(Prefetch('assignments', queryset=OperatorAssignment.objects.filter(
        ended_at__isnull=True).select_related('operator'), to_attr='current_assignments'))


def assignment_data(item):
    result = fields(item, 'id source started_at ended_at reason operator_id')
    result.update(operator_name=item.operator.full_name, assigned_by_id=str(item.assigned_by_id),
                  assigned_by_name=item.assigned_by.full_name)
    return result


def summary(report):
    assignments = getattr(report, 'current_assignments', None)
    item = (assignments[0] if assignments else None) if assignments is not None else report.assignments.filter(ended_at__isnull=True).select_related('operator').first()
    result = fields(report, 'id revision workflow_status validation_status publication_status submitted_at closed_at')
    card = report.official_card_version
    result.update(event_type=card.data.get('event_type') if card else None,
        operator_id=str(item.operator_id) if item else None,
        operator_name=item.operator.full_name if item else None,
        official_version=card.version_number if card else None)
    return result


def can_metadata(actor, report):
    perms = effective_permissions(actor)
    return (actor.role == 'ADMIN' and bool({'monitor_report', 'assign_report'} & perms) or
            'view_assigned_report' in perms and is_assignee(actor, report))


def audit_data(item):
    return dict(fields(item, 'id created_at actor_role report_id action object_type object_id before after request_id'),
                actor_id=str(item.actor_id) if item.actor_id else None,
                actor_name=('Reporter' if item.actor_role == 'REPORTER' else item.actor.full_name) if item.actor else 'Sistem')


class ReportList(APIView):
    def get(self, request):
        validate_query(request, ['scope', 'q', 'event_type', 'workflow_status', 'validation_status', 'followup_status', 'active', 'unassigned', 'ordering'])
        qs = reports_query(request.user, request.query_params.get('scope', 'assigned'))
        if request.query_params.get('q'):
            value = request.query_params['q'].replace('-', '').strip().lower()
            if len(value) > 32 or any(c not in '0123456789abcdef' for c in value):
                raise ApiProblem('INVALID_PAYLOAD', 'Pencarian menggunakan ID laporan.', 400)
            # UUID textual matching is safe and scope-limited by the queryset.
            qs = qs.filter(id__icontains=value)
        if request.query_params.get('event_type'):
            value = serializers.ChoiceField(choices=['FLOOD', 'FIRE', 'EARTHQUAKE', 'ACCIDENT']).run_validation(request.query_params['event_type'])
            qs = qs.filter(official_card_version__data__event_type=value)
        if request.query_params.get('workflow_status'):
            value = serializers.ChoiceField(choices=['SUBMITTED', 'ASSIGNED', 'IN_REVIEW', 'FOLLOW_UP', 'CLOSED']).run_validation(request.query_params['workflow_status'])
            qs = qs.filter(workflow_status=value)
        if 'validation_status' in request.query_params:
            value = serializers.ChoiceField(choices=['NOT_REVIEWED', 'VALID', 'INVALID', 'INCONCLUSIVE']).run_validation(request.query_params['validation_status'])
            qs = qs.filter(validation_status=value)
        if 'followup_status' in request.query_params:
            value = serializers.ChoiceField(choices=['PENDING', 'DONE', 'CANCELLED']).run_validation(request.query_params['followup_status'])
            qs = qs.filter(followups__status=value).distinct()
        if 'active' in request.query_params:
            value = serializers.ChoiceField(choices=['true', 'false']).run_validation(request.query_params['active'])
            qs = qs.exclude(workflow_status='CLOSED') if value == 'true' else qs.filter(workflow_status='CLOSED')
        if 'unassigned' in request.query_params:
            value = serializers.ChoiceField(choices=['true', 'false']).run_validation(request.query_params['unassigned'])
            current = OperatorAssignment.objects.filter(report_id=OuterRef('pk'), ended_at__isnull=True)
            qs = qs.annotate(workspace_assigned=Exists(current)).filter(workspace_assigned=value == 'false')
        ordering = serializers.ChoiceField(choices=['submitted_at', '-submitted_at']).run_validation(request.query_params.get('ordering', '-submitted_at'))
        pager = SilarPagination(); page = pager.paginate_queryset(qs.order_by(ordering, 'id'), request)
        return pager.get_paginated_response([summary(row) for row in page])


class ReportDetail(APIView):
    def get(self, request, pk):
        reject_query(request); services.staff(request.user)
        report = get_object_or_404(Report.objects.select_related('official_card_version', 'latest_review'), pk=pk)
        services.official(report)
        if not can_metadata(request.user, report): raise Http404
        perms = effective_permissions(request.user)
        private = 'view_assigned_report' in perms and is_assignee(request.user, report)
        data = {'report': dict(snapshot(report), **summary(report)), 'private_access': private,
                'assignment': None, 'assignments': [], 'reviews': [], 'followups': [], 'official_card': None,
                'official_bundle': None, 'official_narrative': None, 'ai': None,
                'decision_reason': report.publication_decision_reason if private else None,
                'closure_note': report.closure_note if private else None,
                'close_requirements': services.close_requirements(report),
                'has_active_candidate': services.active_candidate(report), 'history': []}
        for event in AuditEvent.objects.filter(report=report).select_related('actor').order_by('-created_at', '-id')[:100]:
            data['history'].append({'id': str(event.id), 'action': event.action,
                'actor_name': ('Reporter' if event.actor_role == 'REPORTER' else event.actor.full_name) if event.actor else 'Sistem',
                'actor_role': event.actor_role, 'created_at': primitive(event.created_at),
                'states': {key: value for key, value in event.after.items() if key in
                    ['workflow_status', 'validation_status', 'publication_status', 'revision']}})
        assignments = report.assignments.select_related('operator', 'assigned_by').order_by('-started_at', '-id')
        data['assignments'] = [assignment_data(x) for x in assignments]
        data['assignment'] = next((x for x in data['assignments'] if x['ended_at'] is None), None)
        for item in report.reviews.select_related('operator').order_by('-reviewed_at', '-id'):
            row = fields(item, 'id outcome reviewed_at card_version_id operator_id')
            row['operator_name'] = item.operator.full_name
            if private: row['reason'] = item.reason
            data['reviews'].append(row)
        for item in report.followups.select_related('operator').order_by('-created_at', '-id'):
            row = fields(item, 'id status created_at finished_at operator_id')
            row['operator_name'] = item.operator.full_name
            if private: row.update(description=item.description, completion_reason=item.completion_reason)
            data['followups'].append(row)
        if private:
            card = report.official_card_version
            data.update(official_card=card_data(card), official_bundle=bundle_data(card.bundle),
                        official_narrative=narrative_data(card.narrative), ai={
                'sena': dict(fields(card.sena_result, 'id category raw_output model_version'), confidence=float(card.sena_result.confidence)),
                'nara': fields(card.nara_result, 'id raw_output normalized_output normalization_warnings model_version')})
        return Response({'data': data})


class Targets(APIView):
    def get(self, request):
        validate_query(request, []); require_admin(request.user, 'assign_report')
        result = []
        for user in User.objects.filter(role__in=['OPERATOR', 'ADMIN'], is_active=True,
                email_verified_at__isnull=False).order_by('full_name', 'id'):
            if 'view_assigned_report' in effective_permissions(user):
                result.append({'id': str(user.id), 'full_name': user.full_name, 'role': user.role})
        pager = SilarPagination(); page = pager.paginate_queryset(result, request)
        return pager.get_paginated_response(page)


class Dashboard(APIView):
    def get(self, request):
        reject_query(request); services.staff(request.user)
        user = request.user; perms = effective_permissions(user); counts = {}
        if user.role == 'ADMIN':
            if 'monitor_report' in perms or 'assign_report' in perms:
                qs = reports_query(user, 'monitor' if 'monitor_report' in perms else 'assignment')
                active = OperatorAssignment.objects.filter(report_id=OuterRef('pk'), ended_at__isnull=True)
                counts.update(official=qs.count(), closed=qs.filter(workflow_status='CLOSED').count(),
                    unassigned=qs.exclude(workflow_status='CLOSED').annotate(taken=Exists(active)).filter(taken=False).count())
            if 'manage_operator' in perms:
                counts['operators'] = User.objects.filter(role='OPERATOR', is_active=True, email_verified_at__isnull=False).count()
        if 'view_queue' in perms: counts['queue'] = reports_query(user, 'queue').count()
        if 'view_assigned_report' in perms:
            qs = reports_query(user, 'assigned')
            counts.update(assigned=qs.exclude(workflow_status='CLOSED').count(),
                review_pending=qs.filter(validation_status='NOT_REVIEWED').exclude(workflow_status='CLOSED').count(),
                followup_pending=qs.filter(followups__status='PENDING').exclude(workflow_status='CLOSED').distinct().count())
        primary = 'monitor' if user.role == 'ADMIN' and 'monitor_report' in perms else 'assignment' if user.role == 'ADMIN' and 'assign_report' in perms else 'queue' if 'view_queue' in perms else 'assigned' if 'view_assigned_report' in perms else None
        latest = [summary(x) for x in reports_query(user, primary).order_by('-submitted_at', 'id')[:5]] if primary else []
        activity = [fields(x, 'id created_at message report_id') for x in Notification.objects.filter(recipient=user).order_by('-created_at')[:4]]
        return Response({'data': {'counts': counts, 'reports': latest, 'scope': primary,
                                  'activities': activity, 'generated_at': primitive(timezone.now())}})


class Audit(APIView):
    def get(self, request):
        validate_query(request, ['actor_id', 'report_id', 'action', 'operator_id']); allowed(request.user, 'view_audit')
        qs = AuditEvent.objects.select_related('actor').order_by('-created_at', 'id')
        if request.user.role != 'ADMIN':
            qs = qs.filter(report__assignments__operator=request.user, report__assignments__ended_at__isnull=True)
        for field in ['actor_id', 'report_id']:
            if request.query_params.get(field):
                value = serializers.UUIDField().run_validation(request.query_params[field]); qs = qs.filter(**{field: value})
        if request.query_params.get('action'): qs = qs.filter(action=request.query_params['action'])
        if request.query_params.get('operator_id'):
            require_admin(request.user, 'manage_operator')
            value = serializers.UUIDField().run_validation(request.query_params['operator_id'])
            qs = qs.filter(object_type='User', object_id=value)
        pager = SilarPagination(); page = pager.paginate_queryset(qs, request)
        return pager.get_paginated_response([audit_data(x) for x in page])


class Monitoring(APIView):
    def get(self, request):
        reject_query(request); allowed(request.user, 'monitor_services')
        started = perf_counter()
        with connection.cursor() as cursor: cursor.execute('SELECT 1'); cursor.fetchone()
        now = timezone.now(); qs = AnalysisRun.objects.all(); last_day = qs.filter(started_at__gte=now-timedelta(days=1))
        try:
            deadline = timedelta(seconds=float(getattr(settings, 'ANALYSIS_DEADLINE_SECONDS', 240)))
            if deadline.total_seconds() <= 0: deadline = timedelta(seconds=240)
        except (TypeError, ValueError, OverflowError):
            deadline = timedelta(seconds=240)
        return Response({'data': {'checked_at': primitive(now), 'database': 'READY',
            'database_response_ms': round((perf_counter()-started)*1000, 2),
            'analysis_capacity': settings.ANALYSIS_CAPACITY,
            'running': qs.filter(status__in=['RUNNING', 'UNKNOWN']).count(),
            'unknown': qs.filter(status='UNKNOWN').count(),
            'overdue': qs.filter(status__in=['RUNNING', 'UNKNOWN'], started_at__lt=now-deadline).count(),
            'succeeded_24h': last_day.filter(status='SUCCEEDED').count(), 'failed_24h': last_day.filter(status='FAILED').count()}})


class Mutation(APIView):
    def post(self, request, pk, **kwargs):
        reject_query(request)
        get_object_or_404(Report, pk=pk)
        body = self.body_class(data=request.data); body.is_valid(raise_exception=True)
        return response_mutation(self.operation(request.user, pk, request.headers.get('Idempotency-Key'),
            body.validated_data, request.request_id, **kwargs))


class ClaimView(Mutation):
    body_class = Revision; operation = staticmethod(services.claim)


class AssignmentView(Mutation):
    body_class = Assignment; operation = staticmethod(services.assign)


class ReviewView(Mutation):
    body_class = Review; operation = staticmethod(services.review)


class FollowupView(Mutation):
    body_class = Followup; operation = staticmethod(services.followup)


class FinishFollowupView(Mutation):
    body_class = FinishFollowup; operation = staticmethod(services.followup)


class DecisionView(Mutation):
    body_class = Decision; operation = staticmethod(services.decide)


class CloseView(Mutation):
    body_class = Closure; operation = staticmethod(services.close)
