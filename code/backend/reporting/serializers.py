from datetime import datetime
from uuid import UUID
from rest_framework import serializers
from common.api import StrictSerializer
from core.permissions import effective_permissions, is_assignee


class EvidenceUpload(StrictSerializer):
    type = serializers.ChoiceField(choices=['TEXT', 'AUDIO', 'IMAGE'])
    text_content = serializers.CharField(required=False, trim_whitespace=False, max_length=5000)
    file = serializers.FileField(required=False, allow_empty_file=False)
    expected_revision = serializers.IntegerField(min_value=1)

    def validate(self, data):
        is_text = data['type'] == 'TEXT'
        if is_text:
            if 'file' in data or not data.get('text_content', '').strip():
                raise serializers.ValidationError({'text_content': ['TEXT memerlukan teks nonkosong tanpa file.']})
        elif 'text_content' in data or 'file' not in data:
            raise serializers.ValidationError({'file': ['AUDIO/IMAGE memerlukan satu file tanpa text_content.']})
        return data


class BundleCreate(StrictSerializer):
    evidence_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=5)
    expected_revision = serializers.IntegerField(min_value=1)

    def validate_evidence_ids(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError('Bukti tidak boleh dipilih dua kali.')
        return value


def primitive(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat().replace('+00:00', 'Z')
    return value


def fields(obj, names):
    return {name: primitive(getattr(obj, name)) for name in names.split()}


def snapshot(report):
    return fields(report, 'id revision input_revision preparation_status workflow_status validation_status '
                  'publication_status active_bundle_id active_narrative_id current_card_version_id '
                  'official_card_version_id active_publication_candidate_id published_version_id submitted_at closed_at')


def evidence_data(item):
    data = fields(item, 'id created_at report_id type text_content original_name mime_type byte_size sha256 uploaded_by_id')
    data['uploaded_by'] = data.pop('uploaded_by_id')
    return data


def bundle_data(bundle):
    if bundle is None:
        return None
    data = fields(bundle, 'id created_at report_id version_number source_digest created_by_id')
    data['created_by'] = data.pop('created_by_id')
    data['items'] = [{'position': x.position, 'evidence': evidence_data(x.evidence)}
                     for x in bundle.items.select_related('evidence').order_by('position')]
    return data


def narrative_data(obj):
    if obj is None:
        return None
    data = fields(obj, 'id created_at report_id bundle_id parent_id producer_run_id version_number text origin created_by_id')
    data['created_by'] = data.pop('created_by_id')
    return data


def card_data(obj):
    if obj is None:
        return None
    data = fields(obj, 'id created_at report_id bundle_id narrative_id sena_result_id nara_result_id parent_id '
                  'version_number source_kind data uncertain uncertain_reasons fusion_version created_by_id')
    data['created_by'] = data.pop('created_by_id')
    return data


def run_data(run):
    if run is None:
        return None
    data = fields(run, 'id created_at report_id bundle_id input_narrative_id output_narrative_id used_transcript_id '
                  'input_revision mode route status stage model_versions started_at finished_at error_code timings_ms')
    data['used_transcript'] = None
    if run.used_transcript_id:
        data['used_transcript'] = fields(run.used_transcript, 'id created_at report_id evidence_id analysis_run_id text model_version duration_ms')
    data['output_narrative'] = narrative_data(run.output_narrative)
    sena = getattr(run, 'sena_result', None)
    data['sena'] = fields(sena, 'id created_at analysis_run_id narrative_id category raw_output model_version') if sena else None
    if sena:
        data['sena']['confidence'] = float(sena.confidence)
    nara = getattr(run, 'nara_result', None)
    data['nara'] = fields(nara, 'id created_at analysis_run_id narrative_id raw_output normalized_output normalization_warnings model_version') if nara else None
    return data


def summary_data(report):
    data = fields(report, 'id revision preparation_status workflow_status validation_status publication_status created_at submitted_at closed_at')
    card = report.official_card_version if report.submitted_at else report.current_card_version
    data.update(event_type=card.data.get('event_type') if card else None, uncertain=card.uncertain if card else None)
    return data


def detail_data(report, actor):
    permissions = effective_permissions(actor)
    handler = actor.role in ('OPERATOR', 'ADMIN') and 'view_assigned_report' in permissions and is_assignee(actor, report)
    full = actor.role == 'REPORTER' or handler or 'view_private_evidence' in permissions
    result = dict(report=snapshot(report), active_bundle=None, official_bundle=None, current_card=None,
                  official_card=None, active_narrative=None, latest_run=None, verification=None,
                  assignment=None, latest_review=None, active_candidate=None, published_version=None)
    if full:
        result.update(active_bundle=bundle_data(report.active_bundle),
                      official_bundle=bundle_data(report.official_card_version.bundle) if report.official_card_version_id else None,
                      current_card=card_data(report.current_card_version), official_card=card_data(report.official_card_version),
                      active_narrative=narrative_data(report.active_narrative),
                      latest_run=run_data(report.analysis_runs.order_by('-created_at', '-id').first()))
        if report.current_card_version_id:
            from core.models import HumanVerification
            verification = HumanVerification.objects.filter(card_version_id=report.current_card_version_id).first()
            if verification:
                result['verification'] = fields(verification, 'id created_at report_id card_version_id reporter_id confirmed_at')
    assignment = report.assignments.filter(ended_at__isnull=True).first()
    if assignment:
        result['assignment'] = fields(assignment, 'id created_at report_id operator_id assigned_by_id source started_at ended_at reason'
                                      if full and actor.role != 'REPORTER' else 'id operator_id started_at ended_at')
        if 'assigned_by_id' in result['assignment']:
            result['assignment']['assigned_by'] = result['assignment'].pop('assigned_by_id')
    if report.latest_review_id:
        result['latest_review'] = fields(report.latest_review,
            'id created_at report_id card_version_id assignment_id operator_id outcome reason reviewed_at'
            if full and actor.role != 'REPORTER' else 'id outcome reviewed_at')
    def publication(obj, internal):
        if internal:
            data = fields(obj, 'id created_at report_id card_version_id parent_id version_number data state '
                          'sanitized_by_id approved_by_id approved_at published_by_id published_at cancelled_at cancelled_by_id cancellation_reason')
            for key in ('sanitized_by', 'approved_by', 'published_by', 'cancelled_by'):
                data[key] = data.pop(key + '_id')
            return data
        return dict(id=str(report.id), **obj.data, published_at=primitive(obj.published_at))
    if full and actor.role != 'REPORTER' and report.active_publication_candidate_id:
        result['active_candidate'] = publication(report.active_publication_candidate, True)
    if report.published_version_id:
        result['published_version'] = publication(report.published_version, full and actor.role != 'REPORTER')
    return result
