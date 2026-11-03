"""Resume the frozen cohort after JSON tuple/list normalization, without retries.

The first manifest serializes tuple keywords to JSON arrays. Original freeze()
compares that JSON to raw Python tuples on resume. Normalize asdict through JSON;
retain every original source hash, prompt, case, price and budget check.
"""
from dataclasses import asdict
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from architecture_eval import __main__ as experiment
from architecture_eval.provider import Budget, canonical


def json_asdict(value):
    return json.loads(canonical(asdict(value)))


def main():
    config=json.loads(experiment.CONFIG.read_text())
    budget=Budget(experiment.ROOT,config)
    with experiment.controller_lock():
        with patch.object(experiment,"asdict",json_asdict):
            try:
                experiment.run(config,budget)
            finally:
                experiment.report(config,budget)


if __name__=="__main__":
    main()
