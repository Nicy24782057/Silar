from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from common.api import SilarPagination, reject_query, validate_query
from core.models import AnalysisRun, IdempotencyRecord
from core.permissions import can_read_report, effective_permissions, require_report_read

from .output import request_data, run_data
from .serializers import AnalysisCreate
from .services import analyze_report


class AnalysisView(APIView):
    def post(self, request, report_id):
        reject_query(request)
        body = AnalysisCreate(data=request.data)
        body.is_valid(raise_exception=True)
        result = analyze_report(
            actor=request.user, report_id=report_id, attrs=body.validated_data,
            key=request.headers.get("Idempotency-Key"), request_id=request.request_id,
        )
        response = Response(result.payload, status=result.status)
        if result.replayed:
            response["Idempotency-Replayed"] = "true"
        return response


class RunDetailView(APIView):
    def get(self, request, report_id, run_id):
        reject_query(request)
        run = AnalysisRun.objects.select_related(
            "report", "used_transcript", "output_narrative"
        ).filter(pk=run_id, report_id=report_id).first()
        if run is None:
            raise Http404
        require_report_read(request.user, run.report)
        return Response({"data": run_data(
            run, content=can_read_report(request.user, run.report, content=True)
        )})


def readable_requests(user):
    queryset = IdempotencyRecord.objects.filter(actor=user).select_related("report")
    if user.role == Role.REPORTER:
        condition = Q(report__owner=user)
    else:
        permissions = effective_permissions(user)
        condition = Q(pk__in=[])  # No draft visibility for Operator/Admin.
        if "view_assigned_report" in permissions:
            condition |= Q(
                report__submitted_at__isnull=False,
                report__assignments__operator=user, report__assignments__ended_at__isnull=True,
            )
        if user.role == Role.ADMIN and "monitor_report" in permissions:
            condition |= Q(report__submitted_at__isnull=False)
    return queryset.filter(Q(report__isnull=True) | condition).distinct()


def request_output(user, record):
    return request_data(
        record,
        replay_authorized=(
            record.report_id is None
            or can_read_report(user, record.report, content=True)
        ),
    )


class RequestListView(APIView):
    def get(self, request):
        validate_query(request, ["state", "report_id", "include_expired"])
        queryset = readable_requests(request.user)
        if "state" in request.query_params:
            state = serializers.ChoiceField(choices=["RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN"]).run_validation(request.query_params["state"])
            queryset = queryset.filter(state=state)
        if "report_id" in request.query_params:
            report_id = serializers.UUIDField().run_validation(request.query_params["report_id"])
            queryset = queryset.filter(report_id=report_id)
        expired = request.query_params.get("include_expired", "false")
        if expired not in {"true", "false"}:
            raise serializers.ValidationError({"include_expired": ["Gunakan true atau false."]})
        if expired == "false":
            queryset = queryset.filter(
                Q(state__in=["RUNNING", "UNKNOWN"]) | Q(expires_at__gt=timezone.now())
            )
        pager = SilarPagination()
        page = pager.paginate_queryset(queryset.order_by("-created_at", "id"), request)
        return pager.get_paginated_response([request_output(request.user, record) for record in page])


class RequestDetailView(APIView):
    def get(self, request, key):
        reject_query(request)
        record = readable_requests(request.user).filter(key=key).first()
        if record is None:
            raise Http404
        return Response({"data": request_output(request.user, record)})
