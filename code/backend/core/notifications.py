"""In-app event delivery. Call inside the aggregate's mutation transaction.

SLR13/SLR14 can reuse these templates after their own access/state guards.
There is no background delivery, email, or report content in the message.
"""
from django.db import connection

from .models import Notification


MESSAGES = {
    'REPORT_SUBMITTED': 'Laporanmu sudah dikirim dan menunggu pemeriksaan petugas.',
    'REPORT_ASSIGNED': 'Laporan telah ditugaskan kepada petugas.',
    'REVIEW_RECORDED': 'Hasil pemeriksaan laporan telah diperbarui.',
    'FOLLOW_UP_UPDATED': 'Perkembangan penanganan laporan telah diperbarui.',
    'REPORT_CLOSED': 'Penanganan laporan telah ditutup.',
    'REPORT_PUBLISHED': 'Informasi laporan yang telah ditinjau tersedia pada Portal Publik.',
}


def notify(*, recipient, report, kind):
    if not connection.in_atomic_block:
        raise RuntimeError('Notifikasi harus commit bersama tindakan yang memicunya.')
    if kind not in MESSAGES:
        raise ValueError('Jenis event notifikasi tidak dikenal.')
    return Notification.objects.create(
        recipient=recipient, report=report, kind=kind, message=MESSAGES[kind],
    )
