from django.db.models import Exists, OuterRef, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import Role
from accounts.serializers import EmptyBody
from common.api import ApiProblem, SilarPagination, reject_query, validate_query
from core.models import Report, EvidenceItem, OperatorAssignment
from core.permissions import effective_permissions, require_report_read, require_owner_draft
from core.storage import private_media_response
from core.validators import EVENTS
from . import services
from .media import validate_upload
from .serializers import EvidenceUpload, BundleCreate, summary_data, detail_data, evidence_data
from .review_serializers import DeleteDraft


def response_mutation(result):
    response = Response({'data': result.payload}, status=result.status)
    if result.replayed:
        response['Idempotency-Replayed'] = 'true'
    return response


def owner_report(request, pk):
    # Do this before media decoding as well as inside the locked mutation.
    report = get_object_or_404(Report, pk=pk)
    services.authorize_owner(request.user, report)
    return report


class ReportListCreate(APIView):
    def get(self, request):
        validate_query(request, ['scope', 'workflow_status', 'preparation_status', 'validation_status', 'publication_status', 'event_type', 'ordering'])
        actor = request.user
        permissions = effective_permissions(actor)
        default = {'REPORTER': 'owned', 'OPERATOR': 'assigned', 'ADMIN': 'monitor'}[actor.role]
        scope = request.query_params.get('scope', default)
        qs = Report.objects.filter(deleted_at__isnull=True).select_related('official_card_version', 'current_card_version')
        if scope == 'owned' and actor.role == Role.REPORTER:
            qs = qs.filter(owner=actor)
        elif scope == 'assigned' and actor.role in ('OPERATOR', 'ADMIN') and 'view_assigned_report' in permissions:
            qs = qs.filter(submitted_at__isnull=False, assignments__operator=actor, assignments__ended_at__isnull=True)
        elif scope == 'queue' and actor.role in ('OPERATOR', 'ADMIN') and 'view_queue' in permissions:
            active = OperatorAssignment.objects.filter(report_id=OuterRef('pk'), ended_at__isnull=True)
            qs = qs.filter(workflow_status='SUBMITTED', submitted_at__isnull=False).annotate(assigned=Exists(active)).filter(assigned=False)
        elif scope == 'monitor' and actor.role == 'ADMIN' and 'monitor_report' in permissions:
            qs = qs.filter(submitted_at__isnull=False)
        elif scope not in ('owned', 'assigned', 'queue', 'monitor'):
            raise ApiProblem('INVALID_PAYLOAD', 'Scope tidak dikenal.', 400)
        else:
            raise ApiProblem('PERMISSION_DENIED', 'Daftar tidak tersedia untuk kewenangan ini.', 403)
        for name in ('workflow_status', 'preparation_status', 'validation_status', 'publication_status'):
            if name in request.query_params:
                value = request.query_params[name]
                if value not in dict(Report._meta.get_field(name).choices):
                    raise ApiProblem('INVALID_PAYLOAD', 'Filter status tidak dikenal.', 400, {name: ['Nilai tidak dikenal.']})
                qs = qs.filter(**{name: value})
        if 'event_type' in request.query_params:
            category = request.query_params['event_type']
            if category not in (*EVENTS, 'UNCLASSIFIED'):
                raise ApiProblem('INVALID_PAYLOAD', 'Filter kategori tidak dikenal.', 400,
                                 {'event_type': ['Gunakan FLOOD, EARTHQUAKE, FIRE, ACCIDENT atau UNCLASSIFIED.']})
            # Match exactly the same card projection as summary_data, before pagination.
            # JSON null, an absent JSON key and a missing FK are distinct on PostgreSQL.
            def category_match(relation):
                field = relation + '__data__event_type'
                if category == 'UNCLASSIFIED':
                    return Q(**{relation + '__isnull': True}) | Q(**{field + '__isnull': True}) | Q(**{field: None})
                return Q(**{field: category})
            qs = qs.filter(
                (Q(submitted_at__isnull=True) & category_match('current_card_version')) |
                (Q(submitted_at__isnull=False) & category_match('official_card_version')))
        order = request.query_params.get('ordering', '-created_at')
        if order not in ('created_at', '-created_at', 'submitted_at', '-submitted_at'):
            raise ApiProblem('INVALID_PAYLOAD', 'Urutan tidak dikenal.', 400)
        pager = SilarPagination()
        page = pager.paginate_queryset(qs.order_by(order, 'id'), request)
        return pager.get_paginated_response([summary_data(x) for x in page])

    def post(self, request):
        reject_query(request)
        serializer = EmptyBody(data=request.data)
        serializer.is_valid(raise_exception=True)
        return response_mutation(services.create_report(request.user, request.headers.get('Idempotency-Key'), request.request_id))


class ReportDetail(APIView):
    def delete(self, request, pk):
        reject_query(request)
        services.require_reporter(request.user)
        # Retain owner access here only for exact deletion replay; all reads
        # and other operations reject deleted reports through permissions.
        get_object_or_404(Report,pk=pk,owner=request.user)
        body=DeleteDraft(data=request.data)
        body.is_valid(raise_exception=True)
        return response_mutation(services.delete_draft(request.user,pk,request.headers.get('Idempotency-Key'),body.validated_data['expected_revision'],request.request_id))

    def get(self, request, pk):
        reject_query(request)
        report = get_object_or_404(Report, pk=pk)
        require_report_read(request.user, report)
        return Response({'data': detail_data(report, request.user)})


class EvidenceListUpload(APIView):
    parser_classes = [MultiPartParser]

    def get(self, request, pk):
        validate_query(request, [])
        report = owner_report(request, pk)
        require_owner_draft(request.user, report)
        pager = SilarPagination()
        page = pager.paginate_queryset(report.evidence.order_by('created_at', 'id'), request)
        return pager.get_paginated_response([evidence_data(x) for x in page])

    def post(self, request, pk):
        reject_query(request)
        owner_report(request, pk)
        if hasattr(request.data, 'getlist') and any(len(request.data.getlist(k)) != 1 for k in request.data):
            raise ApiProblem('INVALID_PAYLOAD', 'Kirim satu nilai per field dan satu bukti per request.', 400)
        serializer = EvidenceUpload(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        metadata, raw = validate_upload(data)
        return response_mutation(services.upload_evidence(request.user, pk, request.headers.get('Idempotency-Key'),
            metadata, raw, data['expected_revision'], request.request_id))


class BundleCreateView(APIView):
    def post(self, request, pk):
        reject_query(request)
        owner_report(request, pk)
        serializer = BundleCreate(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return response_mutation(services.create_bundle(request.user, pk, request.headers.get('Idempotency-Key'),
            data['evidence_ids'], data['expected_revision'], request.request_id))


class EvidenceMedia(APIView):
    def get(self, request, pk):
        reject_query(request)
        item = get_object_or_404(EvidenceItem.objects.select_related('report'), pk=pk)
        return private_media_response(request.user, item)
