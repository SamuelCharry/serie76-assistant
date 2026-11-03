import sys,os,json,runpy,socket,importlib.util
from pathlib import Path
root=Path(sys.argv[1]); report=Path(sys.argv[2]); arguments=sys.argv[3:]
blocked=[str((root/p).resolve()).replace("\\","/").casefold()+"/" for p in ["data/manual","data/reference","data/reviewed"]]
attempts=[];network=[]
def guard(event,args):
    if event=="open" and isinstance(args[0],(str,bytes,os.PathLike)):
        path=str(Path(os.fsdecode(args[0])).resolve()).replace("\\","/").casefold()
        if any(path.startswith(prefix) for prefix in blocked) or Path(path).name==".env":
            attempts.append(path);raise PermissionError("Reference/secret read forbidden in production acceptance test")
sys.addaudithook(guard)
try:
    open(root/"data/reference/serie76_tablas_extraidas.csv")
except PermissionError:
    self_test=True
else:
    raise AssertionError("Reference guard did not work")
attempts.clear()
def no_network(self,address):
    network.append(str(address));raise PermissionError("Network disabled during offline acceptance run")
socket.socket.connect=no_network
optional={name:bool(importlib.util.find_spec(name)) for name in ["torch","pandas","ydata_profiling","easyocr"]}
sys.argv=["scripts/ingest.py",*arguments]
try:
    runpy.run_path(str(root/"scripts/ingest.py"),run_name="__main__")
finally:
    report.write_text(json.dumps({"guard_self_test_passed":self_test,"forbidden_reference_reads":attempts,"network_attempts":network,"notebook_libraries_present":optional},indent=2),encoding="utf-8")
