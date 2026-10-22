from rest_framework import serializers

from common.api import StrictSerializer


class StrictPositiveInteger(serializers.IntegerField):
    def to_internal_value(self, data):
        if type(data) is not int:
            raise serializers.ValidationError("Harus integer JSON positif.")
        return super().to_internal_value(data)


class AnalysisCreate(StrictSerializer):
    mode = serializers.ChoiceField(choices=["EVIDENCE", "NARRATIVE_REVISION"])
    bundle_id = serializers.UUIDField()
    input_revision = StrictPositiveInteger(min_value=1)
    expected_revision = StrictPositiveInteger(min_value=1)
    narrative_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if attrs["mode"] == "EVIDENCE" and "narrative_id" in attrs:
            raise serializers.ValidationError({"narrative_id": ["Tidak diterima pada mode EVIDENCE."]})
        if attrs["mode"] == "NARRATIVE_REVISION" and "narrative_id" not in attrs:
            raise serializers.ValidationError({"narrative_id": ["Wajib pada mode NARRATIVE_REVISION."]})
        return attrs


def canonical_payload(attrs):
    return {
        key: str(value) if key.endswith("_id") else value
        for key, value in attrs.items()
    }
