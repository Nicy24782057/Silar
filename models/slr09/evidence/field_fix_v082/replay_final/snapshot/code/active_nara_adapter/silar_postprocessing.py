"""Filter lokal untuk negasi, waktu dan fragmen informasi non-dampak.

Tidak mengubah token/span mentah atau menentukan kategori/uncertain.
Fallback tambahan hanya mengambil frasa waktu literal yang ditentukan.
Aturan sengaja terbatas; bukan pendeteksi semantik umum.
"""

from __future__ import annotations

import re


POSTPROCESSING_VERSION = "silar-postprocessing-0.3.0"
_TOKEN = re.compile(r"\w+(?:[-']\w+)*|[^\w\s]", flags=re.UNICODE)
_NEGATED_TIME_PREFIXES = (
    ("bukan",), ("bukan", "pada"),
    ("bukan", "kejadian"), ("bukan", "kejadian", "pada"),
    ("bukan", "peristiwa"), ("bukan", "peristiwa", "pada"),
    ("bukan", "terjadi"), ("bukan", "terjadi", "pada"),
    ("tidak", "terjadi"), ("tidak", "terjadi", "pada"),
    ("tak", "terjadi"), ("tak", "terjadi", "pada"),
)
_SPATIAL_CUES = frozenset({"di", "ke", "dari", "dekat", "depan", "belakang"})
# Hanya frasa lokasi sederhana yang dapat dikenali tanpa menebak kata baru.
# Kata predikat/kalimat tambahan menyebabkan span dipertahankan untuk review.
_LOCATION_HEADS = frozenset({"mall", "mal", "pasar", "pom", "bensin", "jalan"})
_LOCATION_WORDS = _LOCATION_HEADS | _SPATIAL_CUES | {"arah", "sekitar"}


def _words(text: str) -> list[str]:
    return [match.group(0).casefold() for match in _TOKEN.finditer(text)]


def _occurrences(source: list[str], value: list[str]) -> list[int]:
    if not value:
        return []
    return [index for index in range(len(source) - len(value) + 1)
            if source[index:index + len(value)] == value]


def filter_negated_fallback_times(
    narrative: str, values: list[str],
) -> tuple[list[str], list[dict[str, str]]]:
    """Buang fallback hanya jika semua kemunculannya disangkal eksplisit.

    Contoh: 'bukan kejadian hari ini'. Negasi korban di bagian lain kalimat
    tidak berlaku sebagai negasi waktu. TIME-ARG model tidak diproses di sini.
    """
    source = _words(narrative)
    kept, removed = [], []
    for value in values:
        starts = _occurrences(source, _words(value))
        denied = [any(index >= len(prefix) and source[index-len(prefix):index] == list(prefix)
                      for prefix in _NEGATED_TIME_PREFIXES) for index in starts]
        if starts and all(denied):
            removed.append({"field": "time_text", "text": value,
                            "rule": "EXPLICIT_NEGATION_OF_FALLBACK_TIME"})
        else:
            kept.append(value)
    return kept, removed


def filter_spatial_information(
    narrative: str, values: list[str],
) -> tuple[list[str], list[dict[str, str]]]:
    """Buang INFORMATION yang hanya lokasi sederhana dalam konteks spasial.

    Contoh: 'mall' pada 'dari jalan depan mall', atau 'depan pom bensin'.
    'mall rusak' tetap disimpan karena filter tidak menghapus frasa dampak.
    Kosakata di atas membatasi cakupan; lokasi lain belum tentu terdeteksi.
    """
    source = _words(narrative)
    kept, removed = [], []
    for value in values:
        words = _words(value)
        starts = _occurrences(source, words)
        simple_location = (bool(words) and len(words) <= 5
                           and bool(set(words) & _LOCATION_HEADS)
                           and all(word in _LOCATION_WORDS for word in words))
        internal_cue = bool(words and words[0] in _SPATIAL_CUES)
        spatial_occurrences = [internal_cue or (index > 0 and source[index-1] in _SPATIAL_CUES)
                               for index in starts]
        if simple_location and starts and all(spatial_occurrences):
            removed.append({"field": "impacts", "text": value,
                            "rule": "SPATIAL_INFORMATION_NOT_IMPACT"})
        else:
            kept.append(value)
    return kept, removed


def filter_nonimpact_information(narrative, values):
    """Buang frasa komunikasi/latihan/penyangkalan, bukan kategori kejadian.

    Filter lokal pada fragmen INFORMATION, tidak memblokir narasi yang
    mengandung kata simulasi dan tidak menambah label/uncertainty baru.
    """
    kept, removed = [], []
    reporting = re.compile(r'\b(?:memastikan|melaporkan|menjelaskan|menyebut|dibahas|membahas|penyuluhan)\b',re.I)
    effects = re.compile(r'\b(?:terendam|merendam|rusak|merusak|roboh|merobohkan|terluka|meninggal|tewas|menghanguskan|hangus|mengevakuasi|mengungsi|berlarian|memadamkan|melanda|mengguncang|menyebabkan|mengakibatkan|menutup|melibatkan)\b',re.I)
    training = re.compile(r'^(?:(?:menggelar|mengadakan|mengikuti)\s+)?(?:simulasi|latihan)\b',re.I)
    absent_outcome = re.compile(r'^(?:tanpa|nihil)\s+(?:(?:ada|adanya|laporan|mengalami|terjadi)\s+)*(?:korban|luka|cedera|kematian|kerusakan|dampak|kerugian)\b',re.I)
    for value in values:
        folded=value.casefold().strip()
        reject = bool(absent_outcome.search(folded)) or folded in {'tanpa','nihil'}
        reject |= bool(reporting.search(value) and not effects.search(value))
        reject |= bool(training.search(folded) and not effects.search(value))
        reject |= folded in {'tolong','laporan'} or folded.endswith('diminta bersiap menghadapi')
        if reject:removed.append({'field':'impacts','text':value,'rule':'NONIMPACT_INFORMATION_FRAGMENT'})
        else:kept.append(value)
    return kept,removed


def filter_explicitly_unaffected_objects(narrative, values):
    from silar_nara_composition import locate
    denial=re.compile(r'\b(?:tanpa|nihil|tidak|tak|belum)\s+(?:(?:ada|terdapat|kerusakan|pada|yang|korban|luka|jiwa)\s+)*$',re.I)
    kept,removed=[],[]
    for value in values:
        span=locate(value,narrative)
        prior=re.split(r'[.;!?]|\b(?:tetapi|namun|sedangkan)\b',narrative[:span['start']],flags=re.I)[-1] if span else ''
        if span and denial.search(prior+' '):removed.append({'field':'affected_objects','text':value,'rule':'OBJECT_DAMAGE_EXPLICITLY_DENIED'})
        else:kept.append(value)
    return kept,removed


def supplemental_time_fallback(text):
    """Frasa waktu literal tambahan; tetap teks, tidak menjadi timestamp."""
    return [m.group() for m in re.finditer(r'\b(?:sekarang|saat\s+ini|kemarin\s+(?:pagi|siang|sore|malam)|(?:pagi|siang|sore|malam)\s+tadi)\b',text,re.I)]
