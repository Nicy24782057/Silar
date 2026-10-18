"""Local email mailbox, deliberately separate from service logs."""
import os,uuid
from pathlib import Path
from django.core.mail.backends.filebased import EmailBackend as FileEmailBackend

class PrivateFileEmailBackend(FileEmailBackend):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        os.chmod(self.file_path,0o700)
    def _get_filename(self):
        if self._fname is None:self._fname=str(Path(self.file_path)/(uuid.uuid4().hex+'.eml'))
        return self._fname
    def open(self):
        if self.stream is not None:return False
        fd=os.open(self._get_filename(),os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        self.stream=os.fdopen(fd,'ab')
        return True
