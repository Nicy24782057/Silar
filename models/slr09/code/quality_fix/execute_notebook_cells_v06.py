"""Execute pure Python notebook cells, recording actual streams and exceptions.

This is a CPython cell executor, not a native Jupyter kernel. Existing notebook
cells must be plain Python and should declare their own environment inputs.
"""
import argparse
import contextlib
from datetime import datetime,timezone
import io
import sys
import traceback
from pathlib import Path
import nbformat


class Tee(io.StringIO):
    def __init__(self,original):super().__init__();self.original=original
    def write(self,text):self.original.write(text);self.original.flush();return super().write(text)
    def flush(self):self.original.flush()


def execute(source):
    notebook=nbformat.read(source,as_version=4)
    target=source.with_name(source.stem+'_executed.ipynb')
    if target.exists():raise ValueError('Use a new execution output; do not overwrite prior evidence')
    notebook.metadata['execution_engine']='CPYTHON_CELL_EXECUTOR_ACTUAL_EXECUTION_NOT_NATIVE_JUPYTER_KERNEL'
    notebook.metadata['started_at_utc']=datetime.now(timezone.utc).isoformat()
    namespace={'__name__':'__main__'};count=0
    try:
        for cell in notebook.cells:
            if cell.cell_type!='code':continue
            count+=1;cell.execution_count=count;cell.outputs=[]
            stdout,stderr=Tee(sys.stdout),Tee(sys.stderr)
            try:
                with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
                    exec(compile(cell.source,str(source)+f':cell{count}','exec'),namespace)
            except Exception as error:
                cell.outputs.append(nbformat.v4.new_output('error',ename=type(error).__name__,evalue=str(error),traceback=traceback.format_exc().splitlines()))
                notebook.metadata['execution_succeeded']=False
                raise
            finally:
                if stdout.getvalue():cell.outputs.insert(0,nbformat.v4.new_output('stream',name='stdout',text=stdout.getvalue()))
                if stderr.getvalue():cell.outputs.append(nbformat.v4.new_output('stream',name='stderr',text=stderr.getvalue()))
                nbformat.write(notebook,target)
        notebook.metadata['execution_succeeded']=True
    finally:
        notebook.metadata['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        nbformat.write(notebook,target)
        print('Notebook execution recorded:',target,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('notebook',type=Path)
    execute(p.parse_args().notebook)
