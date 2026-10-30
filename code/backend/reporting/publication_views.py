from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api import SilarPagination, reject_query, validate_query
from core.models import Report
from core.validators import EVENTS
from . import publication_serializers as schema, publication_services as services
from .serializers import publication_data
from .views import response_mutation


class PublicationMutation(APIView):
    body_class = schema.Revision

    def post(self, request, pk, version_id=None):
        reject_query(request)
        report = get_object_or_404(Report, pk=pk)
        services._authorize(request.user, report)
        body = self.body_class(data=request.data)
        body.is_valid(raise_exception=True)
        arguments = {'version_id': version_id} if version_id else {}
        result = self.operation(request.user, pk, request.headers.get('Idempotency-Key'),
                                body.validated_data, request.request_id, **arguments)
        return response_mutation(result)


class PublicationDecisionView(PublicationMutation):
    body_class = schema.PublicationDecision
    operation = staticmethod(services.decide)


class PublicationCreateView(PublicationMutation):
    body_class = schema.PublicationCreate
    operation = staticmethod(services.create_candidate)


class PublicationApproveView(PublicationMutation):
    operation = staticmethod(services.approve_candidate)


class PublicationPublishView(PublicationMutation):
    operation = staticmethod(services.publish_candidate)


class PublicationCancelView(PublicationMutation):
    body_class = schema.PublicationCancel
    operation = staticmethod(services.cancel_candidate)


def published_reports():
    # Status PENDING_APPROVAL/APPROVED can coexist with an older published
    # pointer. Only that pointer, never the active candidate, is publicly read.
    return Report.objects.filter(
        published_version__state='PUBLISHED', published_version__published_at__isnull=False,
        published_version__report_id=F('id'),
    ).select_related('published_version').only(
        'id', 'published_version_id', 'published_version__id', 'published_version__data',
        'published_version__published_at',
    )


class PublicReportsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        validate_query(request, ['q', 'event_type', 'general_location'])
        duplicate = {name: ['Gunakan satu nilai parameter.'] for name in request.query_params
                     if len(request.query_params.getlist(name)) != 1}
        if duplicate:
            raise serializers.ValidationError(duplicate)
        reports = published_reports()
        query = request.query_params.get('q', '').strip()
        if query:
            condition = Q()
            for name in ('summary', 'general_location', 'general_impact', 'handling_update'):
                condition |= Q(**{f'published_version__data__{name}__icontains': query})
            reports = reports.filter(condition)
        if 'event_type' in request.query_params:
            category = serializers.ChoiceField(choices=EVENTS).run_validation(request.query_params['event_type'])
            reports = reports.filter(published_version__data__event_type=category)
        location = request.query_params.get('general_location', '').strip()
        if location:
            reports = reports.filter(published_version__data__general_location__icontains=location)
        pager = SilarPagination()
        page = pager.paginate_queryset(reports.order_by('-published_version__published_at', 'id'), request)
        response = pager.get_paginated_response([
            publication_data(report.published_version, internal=False, report=report) for report in page
        ])
        response['Cache-Control'] = 'no-store'
        return response


class PublicReportDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk):
        reject_query(request)
        report = get_object_or_404(published_reports(), pk=pk)
        return Response({'data': publication_data(report.published_version, internal=False, report=report)},
                        headers={'Cache-Control': 'no-store'})
