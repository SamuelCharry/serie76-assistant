"""Reproducible acceptance checks; references stay outside the production process."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalog_ingest.ocr import atomic_json
from evaluate_ingestion import evaluate


def jobs(root):
    manifest = json.loads((root / "run_manifest.json").read_text())
    return [
        json.loads(line) for line in Path(manifest["job_log"]).read_text().splitlines()
    ]


def run(command, log, expected=0):
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(
            command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=1800
        )
    if result.returncode != expected:
        raise AssertionError(
            f"Command returned {result.returncode}, expected {expected}; see {log}"
        )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--python", type=Path, default=ROOT / ".venv-ingest/Scripts/python.exe"
    )
    p.add_argument("--out", type=Path, default=ROOT / "reports/pipeline/acceptance")
    p.add_argument("--scale", action="store_true")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    root = args.out.resolve()
    runtime = args.python.resolve()
    subprocess.run(
        [str(runtime), "scripts/make_pipeline_fixtures.py"], cwd=ROOT, check=True
    )
    fixtures = ROOT / ".cache/pipeline-fixtures"
    driver = root / "guarded_ingest.py"
    guard_report = root / "reference_isolation.json"
    guarded_output = ROOT / "data/processed/acceptance-isolated"
    cold_cache = ROOT / ".cache/acceptance-inference"
    driver.write_text(
        """import sys,os,json,runpy,socket,importlib.util
from pathlib import Path
root=Path(sys.argv[1]); report=Path(sys.argv[2]); arguments=sys.argv[3:]
blocked=[str((root/p).resolve()).replace("\\\\","/").casefold()+"/" for p in ["data/manual","data/reference","data/reviewed"]]
attempts=[];network=[]
def guard(event,args):
    if event=="open" and isinstance(args[0],(str,bytes,os.PathLike)):
        path=str(Path(os.fsdecode(args[0])).resolve()).replace("\\\\","/").casefold()
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
""",
        encoding="utf-8",
    )
    run(
        [
            str(runtime),
            str(driver),
            str(ROOT),
            str(guard_report),
            str(ROOT / "data/raw/series_76_electric_data.pdf"),
            "--out",
            str(guarded_output),
            "--cache",
            str(cold_cache),
        ],
        root / "isolated.log",
    )
    isolated = jobs(guarded_output)[0]
    isolation = json.loads(guard_report.read_text())
    assert (
        not isolation["forbidden_reference_reads"] and not isolation["network_attempts"]
    )
    assert not any(isolation["notebook_libraries_present"].values())
    evaluation = evaluate(
        Path(isolated["output"]) / "catalog.csv",
        ROOT / "data/reference/serie76_tablas_extraidas.csv",
    )
    assert evaluation["status"] == "passed", evaluation["discrepancies"][:10]
    atomic_json(root / "original_evaluation.json", evaluation)
    variants = ROOT / "data/processed/acceptance-variants"
    command = [
        str(runtime),
        "scripts/ingest.py",
        str(fixtures / "unseen-values.pdf"),
        str(fixtures / "unseen-shifted.pdf"),
        str(fixtures / "reordered-pages.pdf"),
        "--out",
        str(variants),
        "--no-images",
    ]
    run(command, root / "variants.log")
    expected = json.loads((fixtures / "unseen-expected.json").read_text())
    variant_results = []
    for job in jobs(variants):
        folder = Path(job["output"])
        if "reordered" in job["input"]:
            e = evaluate(
                folder / "catalog.csv",
                ROOT / "data/reference/serie76_tablas_extraidas.csv",
            )
            assert e["status"] == "passed", e["discrepancies"][:10]
        else:
            with (folder / "catalog.csv").open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == len(expected)
            for row, reference in zip(rows, expected):
                for field, value in reference.items():
                    assert (
                        row[field] == value
                        if field == "base_part_number"
                        else float(row[field]) == value
                    ), (field, row[field], value)
            e = dict(
                status="passed",
                rows=3,
                independent_new_identities=True,
                genuine_decimal_seconds_preserved=True,
            )
        variant_results.append(
            dict(input=job["input"], output=job["output"], evaluation=e)
        )
    atomic_json(root / "variants.json", variant_results)
    isolation_output = ROOT / "data/processed/acceptance-failure-isolation"
    run(
        [
            str(runtime),
            "scripts/ingest.py",
            str(fixtures / "unsupported.pdf"),
            str(fixtures / "broken.pdf"),
            str(fixtures / "unseen-values.pdf"),
            "--out",
            str(isolation_output),
            "--no-images",
        ],
        root / "batch-errors.log",
        expected=2,
    )
    results = jobs(isolation_output)
    assert [j["status"] for j in results] == ["needs_review", "failed", "ready"], (
        results
    )
    for job in results[:2]:
        if "output" in job:
            assert not (Path(job["output"]) / "catalog.csv").exists()
    atomic_json(root / "batch_failure_isolation.json", results)
    run(command, root / "resume.log")
    assert all(j["reused"] for j in jobs(variants))
    summary = dict(
        status="passed",
        original_output=isolated["output"],
        original_evaluation=evaluation,
        reference_and_network_isolation=isolation,
        variants_passed=len(variant_results),
        failure_isolation=True,
        verified_resume=True,
        scale_test="not_requested",
    )
    if args.scale:
        import psutil

        scale_output = ROOT / "data/processed/acceptance-scale-100"
        cmd = [
            str(runtime),
            "scripts/ingest.py",
            str(fixtures / "hundred-pages.pdf"),
            "--out",
            str(scale_output),
            "--cache",
            str(ROOT / ".cache/scale-inference"),
            "--no-images",
        ]
        samples = []
        start = time.perf_counter()
        with (root / "scale.log").open("w", encoding="utf-8") as stream:
            process = subprocess.Popen(
                cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT
            )
            observed = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    rss = observed.memory_info().rss + sum(
                        c.memory_info().rss for c in observed.children(recursive=True)
                    )
                    samples.append(
                        dict(
                            seconds=round(time.perf_counter() - start, 2), rss_bytes=rss
                        )
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                time.sleep(0.25)
            assert process.returncode == 0, (
                f"Scale test failed; see {root / 'scale.log'}"
            )
        scale_job = jobs(scale_output)[0]
        m = json.loads((Path(scale_job["output"]) / "manifest.json").read_text())
        assert (
            m["pages_completed"],
            m["tables"],
            m["rows"],
            m["source_na_rows"],
            m["issues"],
        ) == (100, 175, 1700, 100, 0), m
        scale = dict(
            status="passed",
            pages=100,
            tables=175,
            rows=1700,
            source_na_rows=100,
            elapsed_seconds=round(time.perf_counter() - start, 2),
            peak_rss_bytes=max(s["rss_bytes"] for s in samples),
            samples=samples,
            cache_hits=m["cache_hits"],
            cache_misses=m["cache_misses"],
            output=scale_job["output"],
            scope="100-page volume test repeats the four source pages 25 times; not a heterogeneous-document accuracy benchmark",
        )
        atomic_json(root / "scale-100.json", scale)
        summary["scale_test"] = {k: v for k, v in scale.items() if k != "samples"}
    atomic_json(root / "summary.json", summary)
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k != "original_evaluation"}, indent=2
        )
    )


if __name__ == "__main__":
    main()
