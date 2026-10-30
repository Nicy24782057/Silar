"""SLR14 request schemas, following Technical Reference A4.23 and A6.5."""
from datetime import timezone as datetime_timezone

from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from common.api import StrictSerializer
from core.validators import aware_timestamp


class Revision(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=1)


class PublicationDecision(Revision):
    decision = serializers.ChoiceField(choices=['INTERNAL', 'PREPARE'])
    reason = serializers.CharField(max_length=3000, trim_whitespace=True)


class PublicationOverrides(StrictSerializer):
    # event_type is deliberately absent: the official category is immutable.
    summary = serializers.CharField(max_length=2000, required=False, trim_whitespace=True)
    general_location = serializers.CharField(max_length=500, required=False, allow_null=True, allow_blank=True)
    time_text = serializers.CharField(max_length=300, required=False, allow_null=True, allow_blank=True)
    occurred_at = serializers.CharField(required=False, allow_null=True)
    general_impact = serializers.CharField(max_length=2000, required=False, allow_null=True, allow_blank=True)
    handling_update = serializers.CharField(max_length=2000, required=False, allow_null=True, allow_blank=True)

    def validate_occurred_at(self, value):
        if value is None:
            return None
        if not aware_timestamp(value):
            raise serializers.ValidationError('Gunakan waktu ISO 8601 dengan zona waktu, atau null.')
        return parse_datetime(value).astimezone(datetime_timezone.utc).isoformat().replace('+00:00', 'Z')


class PublicationCreate(Revision):
    parent_id = serializers.UUIDField(allow_null=True)
    data = PublicationOverrides(required=False, default=dict)


class PublicationCancel(Revision):
    reason = serializers.CharField(max_length=3000, trim_whitespace=True)
