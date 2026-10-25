from django.db import transaction
from django.db.models import BooleanField, Case, CharField, F, UUIDField, Value, When
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import EmptyBody
from common.api import SilarPagination, reject_query, validate_query
from core.models import AuditEvent, EvidenceBundle, IncidentCardVersion, NarrativeVersion, Notification, PublicationVersion, Report
from core.permissions import can_read_report, require_report_read
from . import review_services
from .review_serializers import CardRevision, ConfirmCard, NarrativeRevision, SubmitCard
from .serializers import bundle_data, card_data, fields, narrative_data, primitive, publication_data
from .views import owner_report, response_mutation


class ReporterMutation(APIView):
    def post(self, request, pk):
        reject_query(request)
        owner_report(request, pk)
        body = self.body_class(data=request.data)
        body.is_valid(raise_exception=True)
        return response_mutation(self.operation(
            request.user, pk, request.headers.get('Idempotency-Key'), body.validated_data, request.request_id,
        ))


class NarrativeRevisionView(ReporterMutation):
    body_class = NarrativeRevision
    operation = staticmethod(review_services.revise_narrative)


class CardRevisionView(ReporterMutation):
    body_class = CardRevision
    operation = staticmethod(review_services.revise_card)


class VerificationView(ReporterMutation):
    body_class = ConfirmCard
    operation = staticmethod(review_services.confirm_card)


class SubmitView(ReporterMutation):
    body_class = SubmitCard
    operation = staticmethod(review_services.submit_card)


VERSION_MODELS = {
    'EvidenceBundle': EvidenceBundle, 'NarrativeVersion': NarrativeVersion,
    'IncidentCardVersion': IncidentCardVersion, 'PublicationVersion': PublicationVersion,
}


def readable_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    require_report_read(request.user, report)
    return report


def internal_publication_access(actor, report):
    return actor.role != 'REPORTER' and can_read_report(actor, report, content=True)


def version_queryset(actor, report, kind=None):
    queries = []
    full = can_read_report(actor, report, content=True)
    internal = internal_publication_access(actor, report)
    official_card = report.official_card_version
    official_ids = {
        'EvidenceBundle': official_card.bundle_id if official_card else None,
        'NarrativeVersion': official_card.narrative_id if official_card else None,
        'IncidentCardVersion': report.official_card_version_id,
        'PublicationVersion': report.published_version_id,
    }
    for name, model in VERSION_MODELS.items():
        if kind and kind != name:
            continue
        if name != 'PublicationVersion' and not full:
            continue
        query = model.objects.filter(report=report)
        if name == 'PublicationVersion' and not internal:
            query = query.filter(state='PUBLISHED')
        extra = {
            'kind': Value(name, output_field=CharField()),
            'official': Case(When(pk=official_ids[name], then=Value(True)), default=Value(False), output_field=BooleanField()),
        }
        if name != 'IncidentCardVersion':
            extra['source_kind'] = F('origin') if name == 'NarrativeVersion' else Value(None, output_field=CharField())
        if name == 'EvidenceBundle':
            extra['parent_id'] = Value(None, output_field=UUIDField())
        queries.append(query.annotate(**extra).values(
            'id', 'kind', 'version_number', 'parent_id', 'created_at', 'source_kind', 'official',
        ))
    # A SQL UNION allows stable database pagination without loading version bodies.
    if not queries:
        return []
    return queries[0].union(*queries[1:]).order_by('created_at', 'id')


class VersionListView(APIView):
    def get(self, request, pk):
        validate_query(request, ['kind'])
        report = readable_report(request, pk)
        kind = request.query_params.get('kind')
        if kind is not None:
            kind = serializers.ChoiceField(choices=list(VERSION_MODELS)).run_validation(kind)
        pager = SilarPagination()
        page = pager.paginate_queryset(version_queryset(request.user, report, kind), request)
        return pager.get_paginated_response([{key: primitive(value) for key, value in row.items()} for row in page])


class VersionDetailView(APIView):
    def get(self, request, pk, kind, version_id):
        reject_query(request)
        report = readable_report(request, pk)
        model = VERSION_MODELS.get(kind)
        if model is None:
            raise Http404
        if kind == 'PublicationVersion':
            internal = internal_publication_access(request.user, report)
            query = model.objects.filter(report=report)
            if not internal:
                query = query.filter(state='PUBLISHED')
            obj = get_object_or_404(query, pk=version_id)
            data = publication_data(obj, internal=internal, report=report)
        else:
            require_report_read(request.user, report, content=True)
            obj = get_object_or_404(model, pk=version_id, report=report)
            data = {'EvidenceBundle': bundle_data, 'NarrativeVersion': narrative_data, 'IncidentCardVersion': card_data}[kind](obj)
        return Response({'data': {'kind': kind, 'version': data}})


class HistoryView(APIView):
    def get(self, request, pk):
        validate_query(request, [])
        report = readable_report(request, pk)
        pager = SilarPagination()
        page = pager.paginate_queryset(AuditEvent.objects.filter(report=report).order_by('created_at', 'id'), request)
        result = []
        for event in page:
            item = fields(event, 'id action actor_role created_at')
            item['card_version_id'] = event.after.get('card_version_id')
            item['states'] = {key: event.after[key] for key in review_services.STATE_FIELDS if key in event.after}
            result.append(item)
        return pager.get_paginated_response(result)


def notification_data(item):
    return fields(item, 'id created_at report_id kind message read_at')


class NotificationListView(APIView):
    def get(self, request):
        validate_query(request, ['unread'])
        query = Notification.objects.filter(recipient=request.user)
        if 'unread' in request.query_params:
            unread = request.query_params['unread']
            if unread not in ('true', 'false'):
                raise serializers.ValidationError({'unread': ['Gunakan true atau false.']})
            query = query.filter(read_at__isnull=unread == 'true')
        pager = SilarPagination()
        page = pager.paginate_queryset(query.order_by('-created_at', 'id'), request)
        return pager.get_paginated_response([notification_data(item) for item in page])


class NotificationReadView(APIView):
    def patch(self, request, pk):
        reject_query(request)
        body = EmptyBody(data=request.data)
        body.is_valid(raise_exception=True)
        with transaction.atomic():
            item = get_object_or_404(Notification.objects.select_for_update(), pk=pk, recipient=request.user)
            if item.read_at is None:
                item.read_at = timezone.now()
                item.save(update_fields=['read_at'])
        return Response({'data': notification_data(item)})
