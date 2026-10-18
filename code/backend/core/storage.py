import uuid
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse,Http404
from .permissions import require_report_read

class PrivateMediaStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT,base_url=None,file_permissions_mode=0o600,directory_permissions_mode=0o700)
    def url(self,name):
        raise NotImplementedError('Media privat tidak memiliki URL publik.')

def store_validated_media(content):
    """Called by SLR_10 only after size, type, and decoder validation."""
    key='evidence/'+uuid.uuid4().hex
    return PrivateMediaStorage().save(key,content)

def private_media_response(user,evidence):
    require_report_read(user,evidence.report,content=True)
    if evidence.type not in ('AUDIO','IMAGE') or not evidence.file_key:
        raise Http404
    storage=PrivateMediaStorage()
    path=Path(storage.path(evidence.file_key)).resolve()
    try:path.relative_to(Path(settings.PRIVATE_MEDIA_ROOT).resolve())
    except ValueError:raise Http404
    if not storage.exists(evidence.file_key):raise Http404
    response=FileResponse(storage.open(evidence.file_key,'rb'),content_type=evidence.mime_type or 'application/octet-stream',
                          as_attachment=True,filename=evidence.original_name or 'bukti')
    response['Cache-Control']='no-store';response['X-Content-Type-Options']='nosniff'
    return response

