from pathlib import Path
import contextlib,datetime,io,json,os,sys,traceback
import nbformat
B=Path('/workspace/scratch/e5625dd03138/silar09-quality-fix');ROOT=B/'revision_v0.5/models/slr09'
os.environ.update(SLR09_PACKAGE_ROOT=str(ROOT),SLR09_ASSET_DIR=str(B/'assets/CT'),SLR09_TRAIN_OUTPUT=str(B/'training_run_20261019_cpu'),TOKENIZERS_PARALLELISM='false')
source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'notebooks/11_Perbaikan_SENA_CPU_v0.5.ipynb'
notebook=nbformat.read(source,as_version=4);target=source.with_name(source.stem+'_executed.ipynb')
notebook.metadata['execution_engine']='CPYTHON_CELL_EXECUTOR; Jupyter kernel unavailable due local socket restrictions; all Python cells executed'
namespace={'__name__':'__main__'}
class Tee(io.StringIO):
 def __init__(self,original):super().__init__();self.original=original
 def write(self,s):self.original.write(s);self.original.flush();return super().write(s)
 def flush(self):self.original.flush()
count=0
try:
 for cell in notebook.cells:
  if cell.cell_type!='code':continue
  count+=1;cell.execution_count=count;cell.outputs=[]
  out,err=Tee(sys.stdout),Tee(sys.stderr)
  try:
   with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):exec(compile(cell.source,str(source)+f':cell{count}','exec'),namespace)
  except Exception as e:
   cell.outputs.append(nbformat.v4.new_output('error',ename=type(e).__name__,evalue=str(e),traceback=traceback.format_exc().splitlines()))
   raise
  finally:
   if out.getvalue():cell.outputs.insert(0,nbformat.v4.new_output('stream',name='stdout',text=out.getvalue()))
   if err.getvalue():cell.outputs.append(nbformat.v4.new_output('stream',name='stderr',text=err.getvalue()))
   nbformat.write(notebook,target)
finally:
 print('Notebook execution recorded:',target,flush=True)
