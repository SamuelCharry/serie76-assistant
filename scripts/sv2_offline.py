"""Isolated TEST ONLY process: refuse .env access and external network connections."""
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
for key in ('DATABASE_URL', 'OPENROUTER_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY',
            'EMBEDDING_API_KEY', 'LANGSMITH_API_KEY'):
    os.environ.pop(key, None)
os.environ.update(PGHOST='127.0.0.1', PGPORT='55433', PGDATABASE='series76',
                  PGUSER='series76', PGPASSWORD='sv2-local-test-only',
                  SERIES76_SKIP_DOTENV='1', SERIES76_TEST_DB='1',
                  EMBEDDINGS_ENABLED='false', LANGSMITH_TRACING='false',
                  PYTHONPATH=str(ROOT), PYTHONIOENCODING='utf-8',
                  SERIES76_OFFLINE_DB_EXPLICIT='1')


def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        if Path(os.fsdecode(args[0])).name == '.env':
            raise RuntimeError('SV2 forbids reading .env')
    if event == 'socket.connect':
        address = args[1]
        if isinstance(address, tuple) and address[0] not in ('127.0.0.1', 'localhost', '::1'):
            raise RuntimeError('SV2 offline process forbids external network')


sys.addaudithook(audit)
if sys.argv[1] == '-m':
    module, *args = sys.argv[2:]
    sys.argv = [module, *args]
    runpy.run_module(module, run_name='__main__')
else:
    target, *args = sys.argv[1:]
    sys.argv = [target, *args]
    runpy.run_path(str(ROOT / target), run_name='__main__')
