"""Record the existing acceptance-evaluator fixture suite, without model loading."""
import io
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/acceptance'))
suite=unittest.defaultTestLoader.discover(str(ROOT/'code/acceptance'),pattern='test_*.py')
stream=io.StringIO()
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
out=ROOT/'evidence/quality_fix_v083'
(out/'evaluator_tests.txt').write_text(stream.getvalue())
summary=dict(tests_run=result.testsRun,all_passed=result.wasSuccessful(),
    failures=[t.id() for t,_ in result.failures],errors=[t.id() for t,_ in result.errors],
    skipped=len(result.skipped),scope='SYNTHETIC_EVALUATOR_FIXTURES_NOT_HUMAN_REFERENCE_APPROVAL',
    model_inference_executed=False,quality_acceptance_approved=False)
(out/'evaluator_tests.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
if not result.wasSuccessful():print(stream.getvalue())
raise SystemExit(0 if result.wasSuccessful() else 1)
