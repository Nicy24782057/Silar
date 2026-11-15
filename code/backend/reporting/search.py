"""Read-only keyword search inside a Reporter's already owner-scoped queryset."""
import re

from django.db.models import CharField, Exists, OuterRef, Q, Value
from django.db.models.functions import Cast, Replace

from common.api import ApiProblem
from core.models import EvidenceBundleItem, EvidenceItem

SEARCH_MAX_LENGTH = 100
SEARCH_MAX_TERMS = 8


def search_owned_reports(queryset, value):
    value = value.strip()
    terms = value.split()
    if len(value) > SEARCH_MAX_LENGTH or len(terms) > SEARCH_MAX_TERMS or any(ord(c) < 32 for c in value):
        raise ApiProblem('INVALID_PAYLOAD', 'Gunakan maksimal 100 karakter dan 8 kata pencarian.', 400,
                         {'q': ['Pencarian terlalu panjang atau mengandung karakter kontrol.']})
    queryset = queryset.alias(_search_identifier=Replace(Cast('id', CharField()), Value('-'), Value('')))
    for index, term in enumerate(terms):
        # Exists keeps counts/pagination stable even when several text uploads match.
        initial = EvidenceItem.objects.filter(report_id=OuterRef('pk'), type='TEXT', text_content__icontains=term)
        selected = EvidenceBundleItem.objects.filter(
            bundle_id=OuterRef('active_bundle_id'), evidence__report_id=OuterRef('pk'),
            evidence__type='TEXT', evidence__text_content__icontains=term)
        official = EvidenceBundleItem.objects.filter(
            bundle_id=OuterRef('official_card_version__bundle_id'), evidence__report_id=OuterRef('pk'),
            evidence__type='TEXT', evidence__text_content__icontains=term)
        names = [f'_search_{index}_{kind}' for kind in ('initial', 'selected', 'official')]
        queryset = queryset.alias(**dict(zip(names, (Exists(initial), Exists(selected), Exists(official)))))
        draft_source = (Q(active_bundle_id__isnull=True) & Q(**{names[0]: True})) | Q(**{names[1]: True})
        match = (Q(submitted_at__isnull=True) & (Q(active_narrative__text__icontains=term) | draft_source)) | (
            Q(submitted_at__isnull=False) & (Q(official_card_version__narrative__text__icontains=term) | Q(**{names[2]: True})))
        identifier = term.removeprefix('#').replace('-', '')
        if re.fullmatch(r'[0-9a-fA-F]{1,32}', identifier):
            match |= Q(_search_identifier__icontains=identifier)
        queryset = queryset.filter(match)
    return queryset
