from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime

EVENTS = ['FLOOD', 'EARTHQUAKE', 'FIRE', 'ACCIDENT']
EXTRACTION_FIELDS = {'location_text', 'time_text', 'occurred_at', 'involved_parties', 'impacts', 'victims', 'affected_objects'}
PUBLIC_FIELDS = ('event_type', 'summary', 'general_location', 'time_text', 'occurred_at', 'general_impact', 'handling_update')

def aware_timestamp(value):
    try:
        parsed=parse_datetime(value) if isinstance(value,str) else None
        return parsed is not None and parsed.utcoffset() is not None
    except (ValueError,TypeError):return False

def json_object(value):
    if not isinstance(value, dict):
        raise ValidationError('Harus objek JSON.')

def json_array(value):
    if not isinstance(value, list):
        raise ValidationError('Harus array JSON.')

def extracted_data(value, with_event=False):
    json_object(value)
    fields = EXTRACTION_FIELDS | ({'event_type'} if with_event else set())
    if set(value) != fields:
        raise ValidationError('Field informasi terstruktur harus mengikuti A4.22.')
    if with_event and value['event_type'] not in [*EVENTS, None]:
        raise ValidationError('Kategori tidak dikenal.')
    for name, limit in [('location_text', 500), ('time_text', 300)]:
        v = value[name]
        if v is not None and (not isinstance(v, str) or len(v) > limit):
            raise ValidationError(f'{name} tidak valid.')
    if value['occurred_at'] is not None:
        v = value['occurred_at']
        if not aware_timestamp(v):
            raise ValidationError('occurred_at harus waktu ISO 8601 dengan zona waktu, atau null.')
    for name in ('involved_parties', 'impacts', 'victims', 'affected_objects'):
        v = value[name]
        if not isinstance(v, list) or len(v) > 100 or any(not isinstance(x, str) or len(x) > 500 for x in v):
            raise ValidationError(f'{name} harus array string sesuai A4.22.')

def nara_data(value):
    extracted_data(value)

def normalization_warnings(value):
    json_array(value)
    for warning in value:
        if (not isinstance(warning,dict) or set(warning)!={'code','field'}
            or not isinstance(warning['code'],str) or not 1<=len(warning['code'])<=80
            or not isinstance(warning['field'],str) or warning['field'] not in EXTRACTION_FIELDS):
            raise ValidationError('Peringatan normalisasi harus berupa objek code dan field ekstraksi yang sah.')

def card_data(value):
    extracted_data(value, with_event=True)

def public_data(value):
    json_object(value)
    fields = set(PUBLIC_FIELDS)
    if set(value) != fields or value.get('event_type') not in EVENTS:
        raise ValidationError('Field publik tidak sesuai allowlist A4.23.')
    for name, limit in [('summary', 2000), ('general_location', 500), ('time_text', 300), ('general_impact', 2000), ('handling_update', 2000)]:
        v = value[name]
        if v is not None and (not isinstance(v, str) or len(v) > limit):
            raise ValidationError(f'{name} tidak valid.')
    if not isinstance(value['summary'], str) or not value['summary'].strip():
        raise ValidationError('Ringkasan publik wajib diisi.')
    timestamp=value['occurred_at']
    if timestamp is not None:
        if not aware_timestamp(timestamp):
            raise ValidationError('occurred_at publik harus waktu ISO 8601 dengan zona waktu, atau null.')

