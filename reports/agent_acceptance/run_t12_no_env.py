import os
import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
os.chdir(root)
# Capture only DB connection settings from the existing running backend.
# No .env file, no Docker inspect of provider credentials, no secret output.
code = "import os,json; print(json.dumps({k:os.environ[k] for k in ['PGDATABASE','PGUSER','PGPASSWORD']}))"
import json
if os.environ.get('SERIES76_OFFLINE_DB_EXPLICIT') != '1':
    settings = json.loads(subprocess.check_output(['docker','exec','serie76-assistant-backend-1','python','-c',code], text=True))
    os.environ.update(settings)
    os.environ.update(PGHOST='127.0.0.1', PGPORT='5432')
os.environ.update(SERIES76_TEST_DB='1', LANGSMITH_TRACING='false', EMBEDDINGS_ENABLED='false')
for key in ('DATABASE_URL','OPENROUTER_API_KEY','GOOGLE_API_KEY','OPENAI_API_KEY','EMBEDDING_API_KEY','LANGSMITH_API_KEY'):
    os.environ.pop(key, None)
# Refuse every actual .env file read, including accidental reads by test helpers.
def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        name = Path(os.fsdecode(args[0])).name
        if name == '.env':
            raise RuntimeError('T11 forbids reading .env')
sys.addaudithook(audit)
import backend.catalog.cli
with patch.object(backend.catalog.cli, 'local_environment', lambda *a, **k: None):
    if sys.argv[1] == 'tests':
        import unittest
        suite = unittest.defaultTestLoader.discover(str(root / 'tests'))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(not result.wasSuccessful())
    if sys.argv[1] == '-m':
        module, *args = sys.argv[2:]
        sys.argv = [module, *args]
        runpy.run_module(module, run_name='__main__')
        raise SystemExit(0)
    target, *args = sys.argv[1:]
    sys.argv = [target, *args]
    runpy.run_path(str(root / target), run_name='__main__')



