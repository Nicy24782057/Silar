"""Reporter correction contracts (Technical Reference A6.5/A4.22)."""
from rest_framework import serializers

from common.api import StrictSerializer
from core.validators import aware_timestamp


class TextValue(serializers.CharField):
    def to_internal_value(self, value):
        if not isinstance(value, str):
            self.fail('invalid')
        return super().to_internal_value(value)


class NarrativeRevision(StrictSerializer):
    parent_id = serializers.UUIDField()
    text = TextValue(max_length=5000, trim_whitespace=False)
    expected_revision = serializers.IntegerField(min_value=1)

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError('Narasi tidak boleh kosong.')
        return value


class CardPatch(StrictSerializer):
    location_text = TextValue(required=False, allow_null=True, allow_blank=True, max_length=500)
    time_text = TextValue(required=False, allow_null=True, allow_blank=True, max_length=300)
    occurred_at = TextValue(required=False, allow_null=True)
    involved_parties = serializers.ListField(required=False, max_length=100, child=TextValue(max_length=500, allow_blank=True))
    impacts = serializers.ListField(required=False, max_length=100, child=TextValue(max_length=500, allow_blank=True))
    victims = serializers.ListField(required=False, max_length=100, child=TextValue(max_length=500, allow_blank=True))
    affected_objects = serializers.ListField(required=False, max_length=100, child=TextValue(max_length=500, allow_blank=True))

    def validate_occurred_at(self, value):
        if value is not None and not aware_timestamp(value):
            raise serializers.ValidationError('Gunakan ISO 8601 dengan zona waktu atau null.')
        return value

    def validate(self, data):
        if not data:
            raise serializers.ValidationError('Patch tidak boleh kosong.')
        return data


class CardRevision(StrictSerializer):
    parent_id = serializers.UUIDField()
    patch = CardPatch()
    expected_revision = serializers.IntegerField(min_value=1)


class ConfirmCard(StrictSerializer):
    card_version_id = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)


class SubmitCard(ConfirmCard):
    pass


class DeleteDraft(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=1)
